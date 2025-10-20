import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  MenuItem,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material';
import {
  CloudUpload,
  Refresh,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../api/endpoints';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatDateTime, formatNumber } from '../utils/format';
import { toast } from 'react-hot-toast';

const DATA_TYPES = [
  { value: 'candidates', label: 'Candidates' },
  { value: 'entities', label: 'Entities / Donors' },
  { value: 'expenditures', label: 'IE Expenditures' },
];

export const Admin: React.FC = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dataType, setDataType] = useState('candidates');
  const [uploadResult, setUploadResult] = useState<any>(null);

  const { data: syncStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['sync-status'],
    queryFn: adminApi.getSyncStatus,
  });

  const { data: duplicates, isLoading: duplicatesLoading } = useQuery({
    queryKey: ['duplicates'],
    queryFn: adminApi.getDuplicates,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, type }: { file: File; type: string }) =>
      adminApi.uploadCSV(file, type),
    onSuccess: (data) => {
      setUploadResult(data);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      queryClient.invalidateQueries({ queryKey: ['sync-status'] });
      queryClient.invalidateQueries({ queryKey: ['duplicates'] });
      toast.success('File uploaded successfully');
    },
    onError: () => {
      toast.error('Failed to upload file');
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        toast.error('Please select a CSV file');
        return;
      }
      setSelectedFile(file);
      setUploadResult(null);
    }
  };

  const handleUpload = () => {
    if (!selectedFile) {
      toast.error('Please select a file');
      return;
    }
    uploadMutation.mutate({ file: selectedFile, type: dataType });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Admin Panel
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Upload CSV files and manage data synchronization
      </Typography>

      {/* Sync Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2,
            }}
          >
            <Typography variant="h6" fontWeight="bold">
              Sync Status
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() =>
                queryClient.invalidateQueries({ queryKey: ['sync-status'] })
              }
            >
              Refresh
            </Button>
          </Box>

          {statusLoading ? (
            <LoadingSpinner />
          ) : (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Last Update
                  </Typography>
                  <Typography variant="h6">
                    {formatDateTime(syncStatus?.lastUpdate || new Date())}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total Records
                  </Typography>
                  <Typography variant="h6">
                    {formatNumber(syncStatus?.totalRecords || 0)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Candidates
                  </Typography>
                  <Typography variant="h6">
                    {formatNumber(syncStatus?.candidateCount || 0)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Entities
                  </Typography>
                  <Typography variant="h6">
                    {formatNumber(syncStatus?.entityCount || 0)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Expenditures
                  </Typography>
                  <Typography variant="h6">
                    {formatNumber(syncStatus?.expenditureCount || 0)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Reports
                  </Typography>
                  <Typography variant="h6">
                    {formatNumber(syncStatus?.reportCount || 0)}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          )}
        </CardContent>
      </Card>

      {/* CSV Upload */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Upload CSV File
          </Typography>

          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Data Type"
                fullWidth
                select
                value={dataType}
                onChange={(e) => setDataType(e.target.value)}
              >
                {DATA_TYPES.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <input
                type="file"
                accept=".csv"
                style={{ display: 'none' }}
                ref={fileInputRef}
                onChange={handleFileSelect}
              />
              <Button
                variant="outlined"
                fullWidth
                startIcon={<CloudUpload />}
                onClick={() => fileInputRef.current?.click()}
                sx={{ height: '100%' }}
              >
                {selectedFile ? selectedFile.name : 'Select CSV File'}
              </Button>
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                fullWidth
                onClick={handleUpload}
                disabled={!selectedFile || uploadMutation.isPending}
                startIcon={<CloudUpload />}
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Upload File'}
              </Button>
            </Grid>
          </Grid>

          {uploadMutation.isPending && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Processing file...
              </Typography>
            </Box>
          )}

          {uploadResult && (
            <Alert
              severity={uploadResult.success ? 'success' : 'error'}
              icon={uploadResult.success ? <CheckCircle /> : <ErrorIcon />}
              sx={{ mt: 2 }}
            >
              <Typography variant="body2" fontWeight="bold">
                {uploadResult.success ? 'Upload Successful' : 'Upload Failed'}
              </Typography>
              <Typography variant="body2">
                Records Processed: {uploadResult.recordsProcessed}
              </Typography>
              {uploadResult.duplicatesFound > 0 && (
                <Typography variant="body2">
                  Duplicates Found: {uploadResult.duplicatesFound}
                </Typography>
              )}
              {uploadResult.errors && uploadResult.errors.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  {uploadResult.errors.map((error: string, index: number) => (
                    <Typography key={index} variant="caption" display="block">
                      • {error}
                    </Typography>
                  ))}
                </Box>
              )}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Duplicates */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Duplicate Records
          </Typography>

          {duplicatesLoading ? (
            <LoadingSpinner />
          ) : duplicates && duplicates.length > 0 ? (
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Match Fields</TableCell>
                    <TableCell>Existing Record</TableCell>
                    <TableCell>New Record</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {duplicates.map((dup: any) => (
                    <TableRow key={dup.id}>
                      <TableCell>
                        <Chip label={dup.type} size="small" />
                      </TableCell>
                      <TableCell>
                        {dup.matchFields?.join(', ')}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {JSON.stringify(dup.existingRecord).substring(0, 50)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {JSON.stringify(dup.newRecord).substring(0, 50)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Button size="small" variant="outlined" sx={{ mr: 1 }}>
                          Keep Existing
                        </Button>
                        <Button size="small" variant="outlined">
                          Use New
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="info">No duplicate records found</Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

