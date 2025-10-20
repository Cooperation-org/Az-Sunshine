import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import { ArrowBack, Edit } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { candidatesApi } from '../api/endpoints';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { formatCurrency, formatDate, getStatusColor } from '../utils/format';
import { toast } from 'react-hot-toast';

const COLORS = ['#dc2626', '#2563eb', '#059669'];

export const CandidateDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: candidate, isLoading, error } = useQuery({
    queryKey: ['candidate', id],
    queryFn: () => candidatesApi.getById(id!),
    enabled: !!id,
  });

  const togglePledgeMutation = useMutation({
    mutationFn: () => candidatesApi.togglePledge(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate', id] });
      toast.success('Pledge status updated');
    },
    onError: () => {
      toast.error('Failed to update pledge status');
    },
  });

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error || !candidate) {
    return <ErrorMessage message="Failed to load candidate details" fullScreen />;
  }

  const spendingData = [
    { name: 'PAC', value: candidate.spendingByType.pac },
    { name: 'Individual', value: candidate.spendingByType.individual },
    { name: 'Organization', value: candidate.spendingByType.organization },
  ].filter((item) => item.value > 0);

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/candidates')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" fontWeight="bold">
            {candidate.name}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {candidate.race}
          </Typography>
        </Box>
        <Chip
          label={candidate.status}
          color={getStatusColor(candidate.status)}
          sx={{ mr: 2 }}
        />
        {candidate.hasPledged && (
          <Chip label="Pledged" color="success" variant="outlined" />
        )}
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Total IE Spending
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {formatCurrency(candidate.totalSpending)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Contact Information
              </Typography>
              <Typography variant="body1">{candidate.email}</Typography>
              {candidate.phone && (
                <Typography variant="body2" color="text.secondary">
                  {candidate.phone}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Transparency Pledge
              </Typography>
              <Button
                variant={candidate.hasPledged ? 'outlined' : 'contained'}
                color={candidate.hasPledged ? 'success' : 'primary'}
                onClick={() => togglePledgeMutation.mutate()}
                disabled={togglePledgeMutation.isPending}
                fullWidth
              >
                {candidate.hasPledged ? 'Pledged ✓' : 'Mark as Pledged'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Data */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Spending Breakdown */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Spending by Type
              </Typography>
              {spendingData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={spendingData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) =>
                        `${entry.name}: ${formatCurrency(entry.value)}`
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {spendingData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => formatCurrency(value)} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" align="center">
                  No spending data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* IE Expenditures */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Recent Expenditures
              </Typography>
              <TableContainer sx={{ maxHeight: 300 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Spender</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Type</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {candidate.ieExpenditures?.slice(0, 5).map((exp) => (
                      <TableRow key={exp.id}>
                        <TableCell>{exp.spender}</TableCell>
                        <TableCell>{formatCurrency(exp.amount)}</TableCell>
                        <TableCell>
                          <Chip
                            label={exp.supportOppose}
                            size="small"
                            color={
                              exp.supportOppose === 'Support'
                                ? 'success'
                                : 'error'
                            }
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Donors Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Top Donors
          </Typography>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Donor Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell align="right">Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {candidate.donors?.map((donor) => (
                  <TableRow key={donor.id}>
                    <TableCell>{donor.name}</TableCell>
                    <TableCell>
                      <Chip label={donor.type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(donor.amount)}
                    </TableCell>
                    <TableCell align="right">{formatDate(donor.date)}</TableCell>
                  </TableRow>
                ))}
                {(!candidate.donors || candidate.donors.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No donor data available
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

