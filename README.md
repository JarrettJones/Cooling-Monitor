# Cooling Monitor - Real-Time Heat Exchanger Monitoring System

A full-stack web application for real-time monitoring of Heat Exchangers using Redfish API integration with R-SCM devices.

## 🚀 Features

- **Heat Exchanger Management**: Add, edit, and delete heat exchangers with location tracking
- **Real-Time Monitoring**: Live data updates via WebSocket connections
- **Redfish API Integration**: Automatically retrieve temperature, fan speed, and power consumption data
- **Data Visualization**: Interactive charts for historical data analysis
- **Alert System**: Status indicators (Normal, Warning, Critical) based on threshold values
- **Location Tracking**: Organize heat exchangers by city, building, room, and tile

## 🏗️ Architecture

### Backend
- **Python 3.9+** with **FastAPI**
- **MongoDB** for data persistence with **Motor** (async driver)
- **WebSocket** for real-time communication
- **Redfish API Client** (httpx) for R-SCM device integration
- **APScheduler** for automated polling

### Frontend
- **HTML/CSS/JavaScript** (vanilla, no build process)
- **Jinja2** templates for server-side rendering
- **Chart.js** for data visualization (loaded from CDN)
- **No Node.js required** - everything served from Python backend

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Python** (v3.9 or higher) - [Download](https://www.python.org/downloads/)
- **MongoDB** (v6 or higher) - [Download](https://www.mongodb.com/try/download/community)
- **pip** (comes with Python)

## 🛠️ Installation

### 1. Install Python
If you don't have Python 3.9+ installed:
1. Download from [python.org](https://www.python.org/downloads/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```bash
   python --version
   pip --version
   ```

### 2. Install MongoDB
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the setup wizard
3. Start MongoDB service:
   ```bash
   # Windows
   net start MongoDB
   
   # macOS/Linux
   sudo systemctl start mongod
   ```

### 3. Navigate to Project
```bash
cd Cooling-Monitor
```

### 4. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create `.env` file (copy from `.env.example`):
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env`:
```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/cooling_monitor

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Redfish Configuration
REDFISH_USERNAME=admin
REDFISH_PASSWORD=password
REDFISH_VERIFY_SSL=False

# Monitoring Configuration
POLLING_INTERVAL_SECONDS=30

# CORS
CORS_ORIGINS=["http://localhost:8000", "http://127.0.0.1:8000"]
```

## 🚀 Running the Application

### Development Mode

#### Option 1: Run Everything Together
```bash
npm run dev
```
This will start both backend and frontend simultaneously.

#### Option 2: Run Separately
```bash
# Terminal 1 - Backend
npm run dev:backend

# Terminal 2 - Frontend
npm run dev:frontend
Make sure MongoDB is running, then:

```bash
# Make sure virtual environment is activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Start the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the shortcut:
```bash
python app/main.py
```

The application will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (FastAPI automatic docs)
- **Alternative API Docs**: http://localhost:8000/redoc

### Production Mode

For production deployment:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or using gunicorn:
```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000pi/monitoring/latest` - Get latest data for all heat exchangers
- `GET /api/monitoring/:heatExchangerId` - Get monitoring data history
- `GET /api/monitoring/:heatExchangerId/statistics` - Get statistics

### Health Check
- `GET /api/health` - Check API status

## 🔌 Redfish API Integration

The application uses Redfish API to communicate with R-SCM devices. It retrieves:
- **Thermal Data**: Temperature readings from sensors
- **Fan Data**: Fan speed in RPM
- **Power Data**: Power consumption in Watts

### Redfish Endpoints Used
- `/redfish/v1/Chassis/1/Thermal` - Temperature and fan data
- `/redfish/v1/Chassis/1/Power` - Power consumption data

### Configuration
Update credentials in `backend/.env`:
```env
REDFISH_USERNAME=your_username
REDFISH_PASSWORD=your_password
```

## 📊 Data Models

### Heat Exchanger
```typescript
{
  name: string;
  rscmIp: string;
  location: {
    city: string;
    building: string;
    room: string;
    tile: string;
  };
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

### Monitoring Data
```typescript
{
  heatExchangerId: ObjectId;
  timestamp: Date;
  temperature: number;
  fanSpeed: number;
  powerConsumption: number;
  humidity?: number;
  status: 'normal' | 'warning' | 'critical';
  rawData: any;
}
```

## 🎯 Usage

### Adding a Heat Exchanger
1. Click "Add Heat Exchanger" in the navigation
2. Fill in the form:
   - **Name**: Unique identifier
   - **R-SCM IP**: IP address of the R-SCM device
   - **Location**: City, Building, Room, Tile
3. Click "Create"

The system will test the connection to the R-SCM device before saving.

### Viewing Real-Time Data
1. On the Dashboard, all heat exchangers are displayed with their latest readings
2. Click "View Details" to see detailed charts and history
3. Look for the 🟢 Live indicator to confirm WebSocket connection

### Monitoring Status
- **🟢 Normal**: Temperature < 70°C
- **🟡 Warning**: Temperature 70-80°C
- **🔴 Critical**: Temperature > 80°C

## 🔧 Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
# Windows
sc quer 8000 is in use, update the port number in:
- `.env` (API_PORT)
- Or specify when running: `uvicorn app.main:app --port 8080ngod
```

### Port Already in Use
If ports 3000 or 3001 are in use, update the port numbers in:
- `backend/.env` (PORT)
- `frontend/.env` (VITE_API_URL)
- `backend/src/server.ts`

### Redfish Connection Failed
- Verify the R-SCM IP address is correct and reachable
- Check Redfish credentials in `backend/.env`
- Ensure the R-SCM device supports Redfish API v1

### WebSocket Not Connecting
- Check that the backend WebSocket URL matches in `frontend/.env`
- WebSocket connects to same host as web interface
- Check browser console for connection errors
- Verify no firewall is blocking WebSocket connections
│   ├── models/
│   │   ├── __init__.py
│   │   ├── heat_exchanger.py
│   │   └── monitoring_data.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── heat_exchangers.py
│   │   └── monitoring.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── redfish_client.py
│   │   ├── monitoring_service.py
│   │   └── websocket_manager.py
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── dashboard.js
│       ├── detail.js
│       └── form.js
├── templates/
│   ├── index.html
│   ├── detail.html
│   └── form.html
├── .env.example
├── .gitignore
├── requirements.txt.tsx
│   │   └── index.css
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── package.json
└── README.md
```

## 🧪 Testing Redfish API

To test Redfish API connectivity:
```bash
curl -k -u admin:password https://192.168.1.100/redfish/v1
```

## 📝 Development Notes

### Polling Interval
Default polling interval is 30 seconds. Adjust in `backend/.env`:
```env
POLLING_INTERVAL=30000  # milliseconds
```


### Test Redfish API Connection
```bash
# Windows PowerShell
Invoke-WebRequest -Uri "https://192.168.1.100/redfish/v1" -SkipCertificateCheck -Credential (Get-Credential)

# Or using Python
python -c "import httpx; print(httpx.get('https://192.168.1.100/redfish/v1', auth=('admin', 'password'), verify=False).json())"
```

### Run the Application in Test Mode
```bash
pytest  # If you add tests later
The Redfish client accepts self-signed certificates by default. For production, consider proper certificate validation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch.env`:
```env
POLLING_INTERVAL_SECONDS=30

## 📄 Licenselogs
3. Check Python application logs (console output)
4. Check browser console for frontend errors
5. Verify R-SCM device connectivity
6. Use FastAPI automatic docs at http://localhost:8000/docs for API testingly.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review MongoDB and Node.js logs
3. Check browser console for frontend errors
4. Verify R-SCM device connectivity

## 🔮 Future Enhancements

- [ ] User authentication and authorization
- [ ] Email/SMS alerts for critical status
- [ ] Data export functionality
- [ ] Historical data aggregation
- [ ] Multi-tenant support
- [ ] Advanced analytics and reporting
- [ ] Mobile app
