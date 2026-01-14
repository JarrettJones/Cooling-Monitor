# Cooling Monitor - Real-Time Heat Exchanger Monitoring System

## Project Overview
Real-time monitoring web application for Heat Exchangers using Redfish API integration with role-based access control.

## Architecture
- **Backend**: Python/FastAPI with SQLite
- **Frontend**: HTML/CSS/JavaScript (vanilla, no build process)
- **Database**: SQLite with SQLAlchemy async
- **Real-time Communication**: WebSocket
- **API Integration**: Redfish API for R-SCM devices
- **Authentication**: JWT tokens with HTTP-only cookies
- **Authorization**: Role-based access control (Admin/Technician)

## User Roles
- **Admin**: Full access - manage heat exchangers, users, settings, respond to alerts
- **Technician**: View dashboard and respond to alerts only

## Heat Exchanger Model
Each Heat Exchanger requires:
- Name
- R-SCM IP address
- Location: city, building, room, tile

## Features
- Real-time monitoring with WebSocket updates
- Alert management system with acknowledge/resolve workflow
- User authentication and role-based permissions
- Email and Teams notifications (configurable)
- Historical data tracking with charts
- Responsive dashboard with status indicators

## Development Progress
- [x] Create project instructions file
- [x] Scaffold the project structure
- [x] Create Python backend API structure
- [x] Create simple HTML/JS frontend
- [x] Implement authentication system
- [x] Add alert management system
- [x] Implement role-based access control
- [x] Create user management interface
- [x] Update documentation

## Tech Stack Notes
- No Node.js required - pure Python backend
- Frontend uses CDN for Chart.js (no npm/webpack)
- Single integrated application on port 8000
- FastAPI automatic API docs at /docs
- SQLite for simplicity (no separate database server needed)
