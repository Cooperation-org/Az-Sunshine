import React from 'react';
import { Alert, Box } from '@mui/material';

interface ErrorMessageProps {
  message?: string;
  fullScreen?: boolean;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message = 'An error occurred. Please try again.',
  fullScreen = false,
}) => {
  if (fullScreen) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          p: 2,
        }}
      >
        <Alert severity="error" sx={{ maxWidth: 600 }}>
          {message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Alert severity="error">{message}</Alert>
    </Box>
  );
};

