# Arizona Sunshine - Transparency Project Frontend

A comprehensive React + TypeScript frontend for tracking campaign finance and independent expenditures in Arizona politics.

## 🚀 Features

- **Dashboard**: Overview of spending trends, top candidates, and recent activity
- **Candidates**: Manage candidate information, contact status, and pledges
- **Candidate Details**: Deep dive into individual candidate spending and donors
- **Entities**: Track PACs, donors, and organizations
- **Crowd Reports**: Community-submitted political advertisement reports
- **Admin Panel**: CSV upload, data synchronization, and duplicate management

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **React Router v6** - Client-side routing
- **Material UI (MUI)** - Component library
- **Tailwind CSS** - Utility-first CSS
- **React Query** - Data fetching and caching
- **Recharts** - Data visualizations
- **Axios** - HTTP client
- **React Hot Toast** - Toast notifications

## 📦 Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🌐 Environment Variables

Create a `.env` file in the root directory:

```
VITE_API_URL=http://localhost:5000
```

## 📁 Project Structure

```
src/
├── api/              # API client and endpoints
├── components/       # Reusable components
│   ├── common/      # Common UI components
│   └── layout/      # Layout components
├── contexts/        # React contexts
├── hooks/           # Custom hooks
├── layouts/         # Page layouts
├── pages/           # Page components
├── types/           # TypeScript types
├── utils/           # Utility functions
├── App.tsx          # Main app component
└── main.tsx         # Entry point
```

## 🎨 Features in Detail

### Dashboard
- Real-time statistics
- Spending trend charts
- Top candidates visualization
- Recent activity feed

### Candidates Management
- Searchable data grid
- Filter by status
- Inline status editing
- Pagination support

### Candidate Details
- Comprehensive candidate profile
- Spending breakdown charts
- Donor list
- Pledge management

### Entities
- PAC and donor tracking
- Visual contribution charts
- Type-based filtering
- Detailed contribution data

### Crowd Reports
- Submit new reports
- Image/link attachments
- Admin approval workflow
- Status tracking

### Admin Panel
- CSV file upload
- Data synchronization status
- Duplicate detection
- Bulk data management

## 🎨 Theming

The application supports both light and dark modes. Toggle between themes using the button in the navbar.

## 🔧 Development

### Mock Data Mode

By default, the app runs with mock data. To connect to a real backend:

1. Update `USE_MOCK` to `false` in `src/api/endpoints.ts`
2. Ensure your backend API is running
3. Update `VITE_API_URL` in `.env`

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/layout/Sidebar.tsx`

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop (1920px+)
- Laptop (1024px+)
- Tablet (768px+)
- Mobile (320px+)

## 🚀 Deployment

### Netlify

```bash
npm run build
# Deploy the 'dist' folder
```

### Vercel

```bash
npm run build
# Deploy the 'dist' folder
```

## 📄 License

© 2024 Arizona Sunshine Transparency Project

## 🤝 Contributing

This is a transparency project focused on promoting openness in political spending. Contributions are welcome!

---

Built with ❤️ for Arizona transparency

