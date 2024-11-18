File structure
```bash
/csv-app
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       └── App.js
├── docker-compose.yml
└── .gitignore
```

## Back end

### backend/dockerfile
```dockerfile
# Use a slim Python image to keep things lightweight
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the backend application code into the container
COPY . .

# Install dependencies from the requirements.txt file
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### backend/main.py

```python
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd

app = FastAPI()

# Global variable to hold the uploaded CSV data
data = None

# Endpoint to upload the CSV file
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global data
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    
    # Read CSV data into a pandas DataFrame
    contents = await file.read()
    data = pd.read_csv(contents)
    
    return JSONResponse(content={"message": "CSV loaded successfully"})

# Endpoint to get the dimensionality (number of columns)
@app.get("/dimensionality")
def get_dimensionality():
    if data is not None:
        return {"dimensionality": data.shape[1]}
    raise HTTPException(status_code=400, detail="No CSV file uploaded")

# Endpoint to get the column names (schema)
@app.get("/schema")
def get_schema():
    if data is not None:
        return {"schema": list(data.columns)}
    raise HTTPException(status_code=400, detail="No CSV file uploaded")

# Endpoint to get the data types of each column
@app.get("/data-types")
def get_data_types():
    if data is not None:
        return {"data_types": data.dtypes.to_dict()}
    raise HTTPException(status_code=400, detail="No CSV file uploaded")

# Endpoint to get the first 10 values of a specific column
@app.get("/sample/{column}")
def get_sample(column: str):
    if data is not None and column in data.columns:
        return {"sample": data[column].head(10).tolist()}
    raise HTTPException(status_code=400, detail="Invalid column name or no CSV uploaded")
```

### backend/requirements.txt
```text
fastapi
uvicorn
pandas
python-multipart
```

 ## Front end

### frontend/dockerfile
```dockerfile
# Step 1: Use the official Node.js image to build the React app
FROM node:18 AS build

# Set the working directory inside the container
WORKDIR /app

# Copy the React app source code into the container
COPY . .

# Install dependencies and build the React app
RUN npm install
RUN npm run build

# Step 2: Use Nginx to serve the built React app
FROM nginx:alpine

# Copy the built React app from the previous step into Nginx's directory
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80 (default for Nginx)
EXPOSE 80
```

### frontend/package.json
```json
{
  "name": "csv-app",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "axios": "^0.21.1",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-scripts": "4.0.3"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

### frontend/src/app.js

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [columns, setColumns] = useState([]);
  const [dimensionality, setDimensionality] = useState(null);
  const [dataTypes, setDataTypes] = useState({});
  const [sample, setSample] = useState([]);
  const [selectedColumn, setSelectedColumn] = useState('');

  // Handle file input change
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage('');
  };

  // Upload the CSV file to the backend
  const handleFileUpload = async () => {
    if (!file) {
      setMessage('Please select a file.');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMessage(response.data.message);
      fetchDimensionality(); // Fetch additional data after file upload
      fetchSchema();
      fetchDataTypes();
    } catch (error) {
      setMessage('Failed to upload CSV. Please try again.');
    }
  };

  // Fetch the dimensionality (number of columns)
  const fetchDimensionality = async () => {
    try {
      const response = await axios.get('http://localhost:8000/dimensionality');
      setDimensionality(response.data.dimensionality);
    } catch (error) {
      console.error('Error fetching dimensionality:', error);
    }
  };

  // Fetch the schema (column names)
  const fetchSchema = async () => {
    try {
      const response = await axios.get('http://localhost:8000/schema');
      setColumns(response.data.schema);
    } catch (error) {
      console.error('Error fetching schema:', error);
    }
  };

  // Fetch the data types of the columns
  const fetchDataTypes = async () => {
    try {
      const response = await axios.get('http://localhost:8000/data-types');
      setDataTypes(response.data.data_types);
    } catch (error) {
      console.error('Error fetching data types:', error);
    }
  };

  // Fetch sample data for the selected column
  const fetchSample = async () => {
    if (selectedColumn) {
      try {
        const response = await axios.get(`http://localhost:8000/sample/${selectedColumn}`);
        setSample(response.data.sample);
      } catch (error) {
        console.error('Error fetching sample data:', error);
      }
    }
  };

  return (
    <div className="App">
      <h1>CSV File Processor</h1>

      {/* File Upload Section */}
      <input
        type="file"
        accept=".csv"
        onChange={handleFileChange}
      />
      <button onClick={handleFileUpload}>Upload CSV</button>
      <p>{message}</p>

      {/* Show Dimensionality */}
      {dimensionality && (
        <div>
          <h3>Dimensionality: {dimensionality}</h3>
        </div>
      )}

      {/* Show Schema (Column Names) */}
      {columns.length > 0 && (
        <div>
          <h3>Schema (Column Names):</h3>
          <ul>
            {columns.map((col, index) => (
              <li key={index}>{col}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Show Data Types */}
      {Object.keys(dataTypes).length > 0 && (
        <div>
          <h3>Data Types:</h3>
          <ul>
            {Object.entries(dataTypes).map(([col, type]) => (
              <li key={col}>{col}: {type}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Sample Data Dropdown */}
      {columns.length > 0 && (
        <div>
          <h3>Select a column to view a sample (first 10 values):</h3>
          <select
            onChange={(e) => setSelectedColumn(e.target.value)}
            value={selectedColumn}
          >
            <option value="">Select Column</option>
            {columns.map((col, index) => (
              <option key={index} value={col}>{col}</option>
            ))}
          </select>
          <button onClick={fetchSample}>Get Sample</button>

          {sample.length > 0 && (
            <div>
              <h4>Sample Data:</h4>
              <ul>
                {sample.map((value, index) => (
                  <li key={index}>{value}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
```

### Docker compose

### docker-compose.yaml
```yaml
version: '3'
services:
  frontend:
    build:
      context: ./frontend  # Path to your frontend Dockerfile
    ports:
      - "3000:80"  # Expose React app on port 3000 (inside container it's served on port 80)

  backend:
    build:
      context: ./backend  # Path to your backend Dockerfile
    ports:
      - "8000:8000"  # Expose FastAPI on port 8000
```

Build and start both the containers using docker compose from parent folder 
```bash
docker-compose up --build
```