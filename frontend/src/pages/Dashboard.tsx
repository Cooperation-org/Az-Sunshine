import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/endpoints';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { formatCurrency, formatRelativeTime } from '../utils/format';
import { YEARS } from '../utils/constants';
import { TrendingUp, People, AccountBalance, Report } from '@mui/icons-material';

export const Dashboard: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState('2024');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getStats,
  });

  const { data: spendingTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ['spending-trends', selectedYear],
    queryFn: () => dashboardApi.getSpendingTrends(selectedYear),
  });

  const { data: spendingByCandidate, isLoading: candidateLoading } = useQuery({
    queryKey: ['spending-by-candidate'],
    queryFn: dashboardApi.getSpendingByCandidate,
  });

  const { data: recentActivity, isLoading: activityLoading } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: dashboardApi.getRecentActivity,
  });

  if (statsLoading) {
    return <LoadingSpinner fullScreen />;
  }

  const statCards = [
    {
      title: 'Total IE Spending',
      value: formatCurrency(stats?.totalIESpending || 0),
      icon: <TrendingUp fontSize="large" />,
      color: '#dc2626',
    },
    {
      title: 'Total Candidates',
      value: stats?.totalCandidates || 0,
      icon: <People fontSize="large" />,
      color: '#2563eb',
    },
    {
      title: 'Top Donor',
      value: stats?.topDonor?.name || 'N/A',
      subtitle: formatCurrency(stats?.topDonor?.amount || 0),
      icon: <AccountBalance fontSize="large" />,
      color: '#059669',
    },
    {
      title: 'Crowd Reports',
      value: stats?.totalReports || 0,
      icon: <Report fontSize="large" />,
      color: '#d97706',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Overview of campaign finance and independent expenditures
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                background: `linear-gradient(135deg, ${card.color}15 0%, ${card.color}05 100%)`,
                borderLeft: 4,
                borderColor: card.color,
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Box sx={{ color: card.color }}>{card.icon}</Box>
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {card.title}
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {card.value}
                </Typography>
                {card.subtitle && (
                  <Typography variant="caption" color="text.secondary">
                    {card.subtitle}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Spending Trends */}
        <Grid item xs={12} lg={8}>
          <Card>
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
                  Spending Trends
                </Typography>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Year</InputLabel>
                  <Select
                    value={selectedYear}
                    label="Year"
                    onChange={(e) => setSelectedYear(e.target.value)}
                  >
                    {YEARS.map((year) => (
                      <MenuItem key={year} value={year}>
                        {year}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>

              {trendsLoading ? (
                <LoadingSpinner />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={spendingTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis
                      tickFormatter={(value) =>
                        `$${(value / 1000).toFixed(0)}k`
                      }
                    />
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="amount"
                      stroke="#dc2626"
                      strokeWidth={2}
                      name="IE Spending"
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Spending by Candidate */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Top 5 Candidates
              </Typography>
              {candidateLoading ? (
                <LoadingSpinner />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={spendingByCandidate}
                    layout="vertical"
                    margin={{ left: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      type="number"
                      tickFormatter={(value) =>
                        `$${(value / 1000).toFixed(0)}k`
                      }
                    />
                    <YAxis type="category" dataKey="race" width={60} />
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Bar dataKey="amount" fill="#2563eb" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Recent Activity
          </Typography>
          {activityLoading ? (
            <LoadingSpinner />
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Date</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recentActivity?.map((activity) => (
                    <TableRow key={activity.id}>
                      <TableCell>
                        <Chip
                          label={activity.type}
                          size="small"
                          color={
                            activity.type === 'expenditure'
                              ? 'error'
                              : activity.type === 'candidate'
                              ? 'primary'
                              : 'warning'
                          }
                        />
                      </TableCell>
                      <TableCell>{activity.description}</TableCell>
                      <TableCell align="right">
                        {activity.amount
                          ? formatCurrency(activity.amount)
                          : '—'}
                      </TableCell>
                      <TableCell align="right">
                        {formatRelativeTime(activity.date)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

