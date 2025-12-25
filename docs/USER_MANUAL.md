# User Manual (Standard Operating Procedure)

This guide walks you through the standard workflow of using the Logistics Distribution Route Optimization System.

## 1. Access & Login
1.  Open your browser and navigate to the frontend URL (default: `http://localhost:5173`).
2.  **First Time**: Click "Register" to create a new account.
3.  **Login**: Enter your credentials to access the dashboard.

## 2. Master Data Management
Before planning routes, you must populate the system with basic data.

### 2.1 Vehicle Management
**Navigation**: Sidebar -> Vehicle Management (车辆管理)
1.  Click **"Add Vehicle"**.
2.  Enter the vehicle details:
    -   **Name**: E.g., "Truck A", "Van 101".
    -   **Capacity**: The maximum load (e.g., 1000 kg).
3.  Click **"Add"**. Repeat for your entire fleet.

### 2.2 Customer Management
**Navigation**: Sidebar -> Customer Management (客户管理)
1.  Click **"Add Customer"**.
2.  Enter:
    -   **Name**: E.g., "Supermarket A".
    -   **Address**: Full address string. The system will auto-calculate coordinates.
    -   *(Optional)* Manually adjust Latitude/Longitude if needed.
3.  Click **"Add"**.

### 2.3 Product (Goods) Management
**Navigation**: Sidebar -> Goods Management (货物管理)
1.  Click **"Add Product"**.
2.  Enter:
    -   **Name**: E.g., "Rice 10kg".
    -   **Weight**: Weight per unit (e.g., 10.0).
3.  Click **"Add"**.

## 3. Order Creation
**Navigation**: Sidebar -> Order Management (订单管理)
1.  Click **"Add Order"**.
2.  Select a **Customer** from the dropdown.
3.  Add **Items**:
    -   Select a Product.
    -   Enter Quantity.
    -   *(Optional)* Add more items to the same order.
4.  Click **"Create Order"**. The system automatically calculates total weight/demand.

## 4. Intelligent Dispatch (Route Planning)
**Navigation**: Sidebar -> Dispatch Center (调度中心)
1.  **Select Orders**: Check the boxes for all pending orders you want to deliver.
2.  **Select Vehicles**: Check the boxes for available vehicles.
3.  **Depot**: Ensure the correct starting depot is selected/configured.
4.  Click **"Start Dispatch"**.
5.  The system will process the calculation in the background. Wait for the status to change to **Success**.

## 5. Viewing Results
**Navigation**: Sidebar -> Task List (任务列表)
1.  Find your latest task (Task ID).
2.  Click **"View Details"**.
3.  You will see:
    -   **Route Map**: Visual path on the map.
    -   **Stop Sequence**: Ordered list of customers to visit.
    -   **Total Distance**: Estimated travel distance.

---
**Tips**:
-   Ensure customer addresses are accurate for the map to work correctly.
-   If "Dispatch" fails, check if your vehicles have enough capacity for the selected orders.
