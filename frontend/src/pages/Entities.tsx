import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  TextField,
  InputAdornment,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
  Chip,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Search } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { entitiesApi } from '../api/endpoints';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatCurrency, formatNumber } from '../utils/format';
import { ENTITY_TYPES } from '../utils/constants';

const TYPE_COLORS: Record<string, string> = {
  PAC: '#dc2626',
  Individual: '#2563eb',
  Organization: '#059669',
};

export const Entities: React.FC = () => {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['entities', page, pageSize, search, typeFilter],
    queryFn: () =>
      entitiesApi.getAll({
        page: page + 1,
        pageSize,
        search,
        type: typeFilter || undefined,
      }),
  });

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'type',
      headerName: 'Type',
      width: 130,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          sx={{
            bgcolor: `${TYPE_COLORS[params.value as string]}20`,
            color: TYPE_COLORS[params.value as string],
            fontWeight: 600,
          }}
        />
      ),
    },
    {
      field: 'totalContributions',
      headerName: 'Total Contributions',
      width: 180,
      renderCell: (params: GridRenderCellParams) =>
        formatCurrency(params.value as number),
    },
    {
      field: 'numberOfContributions',
      headerName: '# of Contributions',
      width: 150,
      renderCell: (params: GridRenderCellParams) =>
        formatNumber(params.value as number),
    },
    {
      field: 'topRecipient',
      headerName: 'Top Recipient',
      flex: 1,
      minWidth: 150,
    },
    {
      field: 'address',
      headerName: 'Address',
      flex: 1,
      minWidth: 200,
    },
  ];

  // Prepare chart data
  const chartData = data?.data
    .slice(0, 10)
    .map((entity) => ({
      name: entity.name.length > 20 ? entity.name.substring(0, 20) + '...' : entity.name,
      amount: entity.totalContributions,
      type: entity.type,
    }))
    .sort((a, b) => b.amount - a.amount);

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Entities
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Political Action Committees, individuals, and organizations making contributions
      </Typography>

      {/* Chart */}
      <Card sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Top 10 Contributors
        </Typography>
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={120}
                interval={0}
              />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                labelStyle={{ color: '#000' }}
              />
              <Bar dataKey="amount" radius={[8, 8, 0, 0]}>
                {chartData?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={TYPE_COLORS[entry.type]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>

      {/* Filters */}
      <Card sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search entities..."
            size="small"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ flexGrow: 1, minWidth: 200 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={typeFilter}
              label="Type"
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {ENTITY_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Card>

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
    </Box>
  );
};

