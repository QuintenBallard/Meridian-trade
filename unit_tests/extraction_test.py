from unittest.mock import Mock, call

import pytest

from data.raw import extraction


@pytest.fixture
def mocked_services(monkeypatch):
    # Fake environment variables
    monkeypatch.setenv("csv_file_id", "csv-123")
    monkeypatch.setenv("json_file_id", "json-456")
    monkeypatch.setenv("reference_data_id", "reference-789")
    monkeypatch.setenv("bucket_name", "test-bucket")

    payloads = {
        "csv-123": b"csv file contents",
        "json-456": b'{"test": "json contents"}',
        "reference-789": b"reference file contents",
    }

    # Fake Google Drive responses
    files_service = Mock()

    def fake_get_media(fileId):
        request = Mock()
        request.execute.return_value = payloads[fileId]
        return request

    files_service.get_media.side_effect = fake_get_media

    drive = Mock()
    drive.files.return_value = files_service

    credentials = Mock()

    monkeypatch.setattr(
        extraction.google.auth,
        "default",
        Mock(return_value=(credentials, None)),
    )
    monkeypatch.setattr(
        extraction,
        "build",
        Mock(return_value=drive),
    )

    # Fake S3 client
    s3_client = Mock()
    monkeypatch.setattr(
        extraction.boto3,
        "client",
        Mock(return_value=s3_client),
    )

    # Prevent actual waiting during retry tests
    monkeypatch.setattr(extraction.time, "sleep", Mock())

    return s3_client


def test_upload_files_to_s3_uploads_all_three_files(mocked_services):
    status = extraction.upload_files_to_s3()

    assert status is True

    expected_uploads = [
        call(
            Body=b"csv file contents",
            Bucket="test-bucket",
            Key="raw/meridian_trades.csv",
            ContentType="text/csv",
        ),
        call(
            Body=b'{"test": "json contents"}',
            Bucket="test-bucket",
            Key="raw/meridian_trades.json",
            ContentType="application/json",
        ),
        call(
            Body=b"reference file contents",
            Bucket="test-bucket",
            Key="raw/meridian_reference_data.csv",
            ContentType="text/csv",
        ),
    ]

    assert mocked_services.put_object.call_args_list == expected_uploads
    mocked_services.close.assert_called_once()


def test_upload_files_to_s3_retries_temporary_s3_failure(
    mocked_services,
    monkeypatch,
):
    mocked_services.put_object.side_effect = [
        RuntimeError("Temporary S3 error"),
        None,
        None,
        None,
    ]

    status = extraction.upload_files_to_s3()

    assert status is True
    assert mocked_services.put_object.call_count == 4
    extraction.time.sleep.assert_called_once_with(2)