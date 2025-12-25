# API Documentation

Base URL: `http://localhost:8000`

## Authentication

### Login
- **URL**: `/api/token`
- **Method**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`
- **Params**:
  - `username`: string
  - `password`: string
- **Response**: Access Token (Bearer)

### Register User
- **URL**: `/api/users/`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```

### Get Current User
- **URL**: `/api/users/me/`
- **Method**: `GET`
- **Auth**: Required

---

## Core Resources

### Customers
Manage customer locations and details.

- `GET /api/customers/` - List all customers
- `POST /api/customers/` - Create a customer (Auto-geocodes address if x,y missing)
- `GET /api/customers/{id}` - Get customer details
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Delete customer

### Vehicles
Manage the fleet of delivery vehicles.

- `GET /api/vehicles/` - List all vehicles
- `POST /api/vehicles/` - Create a vehicle
  ```json
  {
    "name": "Truck A",
    "capacity": 1000.0
  }
  ```
- `GET /api/vehicles/{id}` - Get vehicle details
- `PUT /api/vehicles/{id}` - Update vehicle
- `DELETE /api/vehicles/{id}` - Delete vehicle

### Depots
Manage warehouse/depot locations.

- `GET /api/depots/` - List depots
- `POST /api/depots/` - Create depot
- `GET /api/depots/{id}` - Get depot details
- `PUT /api/depots/{id}` - Update depot
- `DELETE /api/depots/{id}` - Delete depot

### Products
Manage goods to be delivered.

- `GET /api/products/` - List products
- `POST /api/products/` - Create product
  ```json
  {
    "name": "Widget",
    "weight": 5.0
  }
  ```
- `GET /api/products/{id}` - Get product details

### Orders
Manage delivery orders for customers.

- `GET /api/orders/` - List orders
- `POST /api/orders/` - Create order
  ```json
  {
     "customer_id": 1,
     "items": [
       {"product_id": 1, "quantity": 10}
     ]
  }
  ```
- `GET /api/orders/{id}` - Get order details

---

## Operations & Optimization

### Geocoding
- `GET /api/geocode/autocomplete?text=...` - Get address suggestions
- `POST /api/geocode/address` - Get coordinates for an address string

### Simple Route Optimization (Stateless)
- `POST /api/optimize`
- **Body**: List of locations + algorithm parameters.
- **Returns**: Optimized route sequence and distance (TSP for one vehicle).

### CVRP Task (Single Vehicle)
- `POST /api/tasks/optimize_cvrp`
- **Body**:
  ```json
  {
    "vehicle_id": 1,
    "depot_id": 1,
    "order_ids": [1, 2, 3]
  }
  ```
- **Description**: Optimizes route for *specific* orders using *one* vehicle with capacity constraints.

### Dispatch Center (Multi-Vehicle)
- `POST /api/dispatch/run` (Async)
- **Body**: List of vehicle IDs, order IDs, depot ID.
- **Returns**: `{"task_id": "..."}`
- **Note**: This delegates to Celery.

### Dispatch Status
- `GET /api/dispatch/status/{task_id}`
- **Returns**: Status (`PENDING`, `PROGRESS`, `SUCCESS`, `FAILURE`) and result if ready.
