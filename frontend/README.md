d# Arizona Sunshine - Frontend

React frontend built with Vite, matching the Figma design.

## Design Features

- **Purple Sidebar Navigation** - Elegant gradient sidebar with icon navigation
- **Clean Header** - Search functionality and notifications
- **Donor Entities Page** - Table with purple avatar icons, matching your Figma design
- **Responsive Layout** - Works on desktop and mobile

## Running the Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## Pages

- **Dashboard** (`/`) - Home page with overview
- **Donors** (`/donors`) - Donor entities with table view ✨ (Matches Figma!)
- **Candidates** (`/candidates`) - Candidate listings
- **Expenditures** (`/expenditures`) - Campaign expenditure data

## Color Scheme

- Primary Purple: `#7C6BA6`
- Secondary Purple: `#6B5B95`
- Background: `#F5F5F5`
- Cards: `#FFFFFF`
- Text: `#1F2937`

## Backend Connection

The frontend connects to the Django backend at `http://localhost:8000/api/`

Make sure the backend is running:
```bash
cd backend
python3 manage.py runserver 127.0.0.1:8000
```

## Dependencies

- React 18
- React Router DOM 6
- Axios
- Vite 6

## Project Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Home.jsx/css
│   │   ├── Donors.jsx/css      ← Matches Figma design!
│   │   ├── Candidates.jsx/css
│   │   └── Expenditures.jsx/css
│   ├── App.jsx
│   ├── App.css
│   └── main.jsx
├── index.html
└── package.json
```

