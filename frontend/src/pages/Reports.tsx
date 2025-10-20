import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Add, CheckCircle, Cancel, Link as LinkIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportsApi } from '../api/endpoints';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatDateTime, getStatusColor } from '../utils/format';
import { AD_TYPES } from '../utils/constants';
import { toast } from 'react-hot-toast';
import type { CreateReportInput, CrowdReport } from '../types';

export const Reports: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<CreateReportInput>({
    adType: 'TV',
    description: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['reports', page, pageSize],
    queryFn: () =>
      reportsApi.getAll({
        page: page + 1,
        pageSize,
      }),
  });

  const createMutation = useMutation({
    mutationFn: reportsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      toast.success('Report submitted successfully');
      setDialogOpen(false);
      setFormData({ adType: 'TV', description: '' });
    },
    onError: () => {
      toast.error('Failed to submit report');
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: CrowdReport['status'] }) =>
      reportsApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Report status updated');
    },
    onError: () => {
      toast.error('Failed to update status');
    },
  });

  const handleSubmit = () => {
    if (!formData.description) {
      toast.error('Please provide a description');
      return;
    }
    createMutation.mutate(formData);
  };

  const columns: GridColDef[] = [
    {
      field: 'reporterName',
      headerName: 'Reporter',
      width: 150,
      renderCell: (params: GridRenderCellParams) =>
        params.value || 'Anonymous',
    },
    {
      field: 'adType',
      headerName: 'Ad Type',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip label={params.value} size="small" variant="outlined" />
      ),
    },
    {
      field: 'description',
      headerName: 'Description',
      flex: 1,
      minWidth: 300,
    },
    {
      field: 'candidateName',
      headerName: 'Candidate',
      width: 150,
    },
    {
      field: 'link',
      headerName: 'Link',
      width: 80,
      renderCell: (params: GridRenderCellParams) =>
        params.value ? (
          <IconButton
            size="small"
            href={params.value as string}
            target="_blank"
            rel="noopener noreferrer"
          >
            <LinkIcon fontSize="small" />
          </IconButton>
        ) : null,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          color={getStatusColor(params.value as string)}
        />
      ),
    },
    {
      field: 'createdAt',
      headerName: 'Submitted',
      width: 180,
      renderCell: (params: GridRenderCellParams) =>
        formatDateTime(params.value as string),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          {params.row.status === 'pending' && (
            <>
              <Tooltip title="Approve">
                <IconButton
                  size="small"
                  color="success"
                  onClick={() =>
                    updateStatusMutation.mutate({
                      id: params.row.id,
                      status: 'approved',
                    })
                  }
                >
                  <CheckCircle fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Reject">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() =>
                    updateStatusMutation.mutate({
                      id: params.row.id,
                      status: 'rejected',
                    })
                  }
                >
                  <Cancel fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Crowd Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Community-submitted reports of political advertisements
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setDialogOpen(true)}
        >
          Submit Report
        </Button>
      </Box>

      {/* Data Grid */}
      <Card>
        <DataGrid
          rows={data?.data || []}
          columns={columns}
          rowCount={data?.total || 0}
          loading={isLoading}
          pageSizeOptions={[5, 10, 25, 50]}
          paginationModel={{ page, pageSize }}
          paginationMode="server"
          onPaginationModelChange={(model) => {
            setPage(model.page);
            setPageSize(model.pageSize);
          }}
          disableRowSelectionOnClick
          autoHeight
          sx={{
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
          }}
        />
      </Card>

      {/* Submit Report Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Submit a Report</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Your Name (Optional)"
                fullWidth
                value={formData.reporterName || ''}
                onChange={(e) =>
                  setFormData({ ...formData, reporterName: e.target.value })
                }
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Your Email (Optional)"
                fullWidth
                type="email"
                value={formData.reporterEmail || ''}
                onChange={(e) =>
                  setFormData({ ...formData, reporterEmail: e.target.value })
                }
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Ad Type"
                fullWidth
                select
                value={formData.adType}
                onChange={(e) =>
                  setFormData({ ...formData, adType: e.target.value })
                }
              >
                {AD_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Candidate Name (Optional)"
                fullWidth
                value={formData.candidateName || ''}
                onChange={(e) =>
                  setFormData({ ...formData, candidateName: e.target.value })
                }
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={4}
                required
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Describe what you saw or heard..."
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Link (Optional)"
                fullWidth
                value={formData.link || ''}
                onChange={(e) =>
                  setFormData({ ...formData, link: e.target.value })
                }
                placeholder="https://..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Submitting...' : 'Submit Report'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

