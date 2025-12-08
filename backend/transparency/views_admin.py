"""
Admin API Views for Phase 1 Features
Provides API endpoints for:
- CSV Import
- County Scrapers
- AZ SOS Automation
- SeeTheMoney (FREE alternative to AZ SOS)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.core.management import call_command
from pathlib import Path
import subprocess
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataImportViewSet(viewsets.ViewSet):
    """
    API for CSV data import operations

    Endpoints:
    - POST /api/imports/upload/ - Upload and import CSV file
    - GET /api/imports/history/ - Get import history
    - GET /api/imports/status/<job_id>/ - Check import status
    """

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload and process CSV file

        Request:
            - file: CSV file (multipart/form-data)
            - source: Source identifier (optional)
            - dry_run: Boolean (optional)

        Response:
            {
                "status": "processing",
                "job_id": "import_20241208_123456",
                "message": "Import started",
                "file_name": "data.csv"
            }
        """
        try:
            uploaded_file = request.FILES.get('file')
            source = request.data.get('source', 'web_upload')
            dry_run = request.data.get('dry_run', False) == 'true'

            if not uploaded_file:
                return Response({
                    'status': 'error',
                    'error': 'No file provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate file extension
            if not uploaded_file.name.endswith('.csv'):
                return Response({
                    'status': 'error',
                    'error': 'Only CSV files are supported'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save uploaded file
            upload_dir = Path('/tmp/az_sunshine_uploads')
            upload_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_id = f"import_{timestamp}"
            file_path = upload_dir / f"{job_id}_{uploaded_file.name}"

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            logger.info(f"File uploaded: {file_path}")

            # TODO: Run import in background task (Celery)
            # For now, run synchronously
            try:
                # Run import command
                from io import StringIO
                out = StringIO()

                call_command(
                    'import_csv',
                    str(file_path),
                    source=source,
                    dry_run=dry_run,
                    stdout=out
                )

                output = out.getvalue()

                # Parse output for statistics
                stats = self._parse_import_output(output)

                return Response({
                    'status': 'completed',
                    'job_id': job_id,
                    'file_name': uploaded_file.name,
                    'source': source,
                    'dry_run': dry_run,
                    'statistics': stats,
                    'message': 'Import completed successfully'
                })

            except Exception as e:
                logger.error(f"Import failed: {str(e)}", exc_info=True)
                return Response({
                    'status': 'failed',
                    'job_id': job_id,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _parse_import_output(self, output):
        """Parse import command output for statistics"""
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

        # Simple parsing - can be improved
        for line in output.split('\n'):
            if 'Created:' in line:
                stats['created'] = int(line.split(':')[1].strip())
            elif 'Updated:' in line:
                stats['updated'] = int(line.split(':')[1].strip())
            elif 'Skipped:' in line:
                stats['skipped'] = int(line.split(':')[1].strip())
            elif 'Errors:' in line:
                stats['errors'] = int(line.split(':')[1].strip())

        return stats

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get import history"""
        # TODO: Implement import history tracking
        return Response({
            'status': 'success',
            'imports': []
        })


class ScraperViewSet(viewsets.ViewSet):
    """
    API for county/city scraper operations

    Endpoints:
    - POST /api/scrapers/run/ - Run scraper for specific county
    - GET /api/scrapers/status/<job_id>/ - Check scraper status
    - GET /api/scrapers/results/ - Get latest scraper results
    """

    @action(detail=False, methods=['post'])
    def run(self, request):
        """
        Run county scraper

        Request:
            {
                "county": "maricopa|pima|tucson|all",
                "year": 2024 (optional),
                "headless": true (optional)
            }

        Response:
            {
                "status": "processing",
                "job_id": "scrape_maricopa_20241208_123456",
                "county": "maricopa",
                "message": "Scraper started"
            }
        """
        try:
            county = request.data.get('county', 'all')
            year = request.data.get('year')
            headless = request.data.get('headless', True)

            valid_counties = ['maricopa', 'pima', 'tucson', 'all']
            if county not in valid_counties:
                return Response({
                    'status': 'error',
                    'error': f'Invalid county. Must be one of: {", ".join(valid_counties)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_id = f"scrape_{county}_{timestamp}"

            logger.info(f"Starting scraper: {county}, year={year}, headless={headless}")

            # TODO: Run in background task (Celery)
            # For now, run synchronously
            try:
                from io import StringIO
                out = StringIO()

                args = ['scrape_counties', f'--county={county}']
                if year:
                    args.append(f'--year={year}')
                if not headless:
                    args.append('--no-headless')

                call_command(*args, stdout=out)

                output = out.getvalue()

                return Response({
                    'status': 'completed',
                    'job_id': job_id,
                    'county': county,
                    'year': year,
                    'message': 'Scraper completed successfully',
                    'output': output
                })

            except Exception as e:
                logger.error(f"Scraper failed: {str(e)}", exc_info=True)
                return Response({
                    'status': 'failed',
                    'job_id': job_id,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Scraper request failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def results(self, request):
        """Get latest scraper results from CSV files"""
        try:
            data_dir = Path('/home/mg/Deploy/az_sunshine/backend/data/county_data')

            if not data_dir.exists():
                return Response({
                    'status': 'success',
                    'results': []
                })

            # Get latest CSV files
            csv_files = list(data_dir.glob('*.csv'))
            csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            results = []
            for csv_file in csv_files[:10]:  # Latest 10 files
                results.append({
                    'file_name': csv_file.name,
                    'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat(),
                    'size': csv_file.stat().st_size
                })

            return Response({
                'status': 'success',
                'results': results
            })

        except Exception as e:
            logger.error(f"Failed to get results: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SOSViewSet(viewsets.ViewSet):
    """
    API for AZ Secretary of State automation

    Endpoints:
    - POST /api/sos/download/ - Download database from AZ SOS
    - POST /api/sos/sync/ - Download and import data
    - GET /api/sos/status/ - Check sync status
    """

    @action(detail=False, methods=['post'])
    def download(self, request):
        """
        Download database from AZ SOS

        Request:
            {
                "year": 2024 (optional),
                "quarter": 1 (optional),
                "purchase": false (optional),
                "headless": true (optional)
            }

        Response:
            {
                "status": "processing",
                "job_id": "sos_download_20241208_123456",
                "message": "Download started"
            }
        """
        try:
            year = request.data.get('year')
            quarter = request.data.get('quarter')
            purchase = request.data.get('purchase', False)
            headless = request.data.get('headless', True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_id = f"sos_download_{timestamp}"

            logger.info(f"Starting AZ SOS download: year={year}, quarter={quarter}")

            # TODO: Run in background task (Celery)
            try:
                from io import StringIO
                out = StringIO()

                args = ['sync_sos_data', '--download-only']
                if year:
                    args.append(f'--year={year}')
                if quarter:
                    args.append(f'--quarter={quarter}')
                if purchase:
                    args.append('--purchase')
                if not headless:
                    args.append('--no-headless')

                call_command(*args, stdout=out)

                output = out.getvalue()

                return Response({
                    'status': 'completed',
                    'job_id': job_id,
                    'year': year,
                    'quarter': quarter,
                    'message': 'Download completed successfully',
                    'output': output
                })

            except Exception as e:
                logger.error(f"AZ SOS download failed: {str(e)}", exc_info=True)
                return Response({
                    'status': 'failed',
                    'job_id': job_id,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"AZ SOS request failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Download and import data from AZ SOS

        Request:
            {
                "year": 2024 (optional),
                "quarter": 1 (optional),
                "headless": true (optional)
            }

        Response:
            {
                "status": "processing",
                "job_id": "sos_sync_20241208_123456",
                "message": "Sync started"
            }
        """
        try:
            year = request.data.get('year')
            quarter = request.data.get('quarter')
            headless = request.data.get('headless', True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_id = f"sos_sync_{timestamp}"

            logger.info(f"Starting AZ SOS sync: year={year}, quarter={quarter}")

            # TODO: Run in background task (Celery)
            try:
                from io import StringIO
                out = StringIO()

                args = ['sync_sos_data']
                if year:
                    args.append(f'--year={year}')
                if quarter:
                    args.append(f'--quarter={quarter}')
                if not headless:
                    args.append('--no-headless')

                call_command(*args, stdout=out)

                output = out.getvalue()

                return Response({
                    'status': 'completed',
                    'job_id': job_id,
                    'year': year,
                    'quarter': quarter,
                    'message': 'Sync completed successfully',
                    'output': output
                })

            except Exception as e:
                logger.error(f"AZ SOS sync failed: {str(e)}", exc_info=True)
                return Response({
                    'status': 'failed',
                    'job_id': job_id,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"AZ SOS sync request failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SeeTheMoneyViewSet(viewsets.ViewSet):
    """
    API for SeeTheMoney.az.gov FREE data downloads

    FREE alternative to $25 AZ SOS database!

    Endpoints:
    - POST /api/seethemoney/download/ - Download free data
    - POST /api/seethemoney/sync/ - Download and import data
    """

    @action(detail=False, methods=['post'])
    def download(self, request):
        """
        Download FREE data from SeeTheMoney.az.gov

        Request:
            {
                "year": 2024 (optional),
                "entity_type": "Candidate" (optional: Candidate|PAC|Party|All),
                "headless": true (optional)
            }

        Response:
            {
                "status": "completed",
                "job_id": "stm_download_20241208_123456",
                "message": "Download completed successfully"
            }
        """
        try:
            year = request.data.get('year')
            entity_type = request.data.get('entity_type', 'Candidate')
            headless = request.data.get('headless', True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_id = f"stm_download_{timestamp}"

            logger.info(f"Starting SeeTheMoney download: year={year}, entity={entity_type}")

            # TODO: Run in background task (Celery)
            try:
                from io import StringIO
                out = StringIO()

                args = ['download_seethemoney']
                if year:
                    args.append(f'--year={year}')
                if entity_type:
                    args.append(f'--entity-type={entity_type}')
                if not headless:
                    args.append('--no-headless')

                call_command(*args, stdout=out)

                output = out.getvalue()

                return Response({
                    'status': 'completed',
                    'job_id': job_id,
                    'year': year or 'current',
                    'entity_type': entity_type,
                    'message': 'Download completed successfully (FREE!)',
                    'output': output
                })

            except Exception as e:
                logger.error(f"SeeTheMoney download failed: {str(e)}", exc_info=True)
                return Response({
                    'status': 'failed',
                    'job_id': job_id,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"SeeTheMoney request failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Download and auto-import FREE data from SeeTheMoney.az.gov

        Request:
            {
                "year": 2024 (optional),
                "entity_type": "Candidate" (optional),
                "headless": true (optional)
            }

        Response:
            {
                "status": "completed",
                "job_id": "stm_sync_20241208_123456",
                "message": "Sync completed successfully"
            }
        """
        try:
            year = request.data.get('year')
            entity_type = request.data.get('entity_type', 'Candidate')
            headless = request.data.get('headless', True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_id = f"stm_sync_{timestamp}"

            logger.info(f"SeeTheMoney sync: year={year}, entity={entity_type}")

            # TODO: Run in background task (Celery)
            try:
                from io import StringIO
                out = StringIO()

                args = ['download_seethemoney', '--import']
                if year:
                    args.append(f'--year={year}')
                if entity_type:
                    args.append(f'--entity-type={entity_type}')
                if not headless:
                    args.append('--no-headless')

                call_command(*args, stdout=out)

                output = out.getvalue()

                return Response({
                    'status': 'completed',
                    'job_id': job_id,
                    'year': year or 'current',
                    'entity_type': entity_type,
                    'message': 'Data downloaded and imported successfully (FREE!)',
                    'output': output
                })

            except Exception as e:
                logger.error(f"SeeTheMoney sync failed: {str(e)}", exc_info=True)
                return Response({
                    'status': 'failed',
                    'job_id': job_id,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"SeeTheMoney sync request failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
