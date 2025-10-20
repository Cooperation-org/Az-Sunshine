import React from 'react';
import { Box, Container, Typography, Link } from '@mui/material';

export const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        bgcolor: 'background.paper',
        borderTop: 1,
        borderColor: 'divider',
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          © {new Date().getFullYear()} Arizona Sunshine Transparency Project.
          Data sourced from{' '}
          <Link
            href="https://azsos.gov"
            target="_blank"
            rel="noopener noreferrer"
            color="primary"
          >
            Arizona Secretary of State
          </Link>
          .
        </Typography>
        <Typography
          variant="caption"
          color="text.secondary"
          align="center"
          display="block"
          sx={{ mt: 1 }}
        >
          Promoting transparency in political spending.
        </Typography>
      </Container>
    </Box>
  );
};

