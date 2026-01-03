import random
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models import sql_models as models
from app.core import security as auth

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

def clear_data(db: Session):
    print("Cleaning up existing data...")
    # Delete in order of dependencies
    db.query(models.TaskStop).delete()
    db.query(models.Task).delete()
    db.query(models.OrderProduct).delete()
    db.query(models.Order).delete()
    db.query(models.Customer).delete()
    db.query(models.Product).delete()
    db.query(models.Vehicle).delete()
    db.query(models.Depot).delete()
    db.query(models.User).delete()
    db.commit()

def seed_data():
    db = SessionLocal()
    try:
        clear_data(db)
        print("Starting data seeding (Chinese Version)...")
        
        # 1. Seed User
        print("Creating default admin user...")
        hashed_password = auth.get_password_hash("password123")
        user = models.User(username="admin", hashed_password=hashed_password)
        db.add(user)

        # 2. Seed Depots (Need 10+)
        print("Creating depots across major cities...")
        major_cities = [
            ("上海", 121.4737, 31.2304, ["总仓", "浦东分拨", "徐汇中转", "静安配送", "虹桥枢纽"]),
            ("北京", 116.4074, 39.9042, ["朝阳分拨", "海淀中转", "大兴物流", "丰台配送"]),
            ("广州", 113.2644, 23.1291, ["天河分仓", "白云物流", "越秀配送"]),
            ("深圳", 114.0579, 22.5431, ["南山科技园仓", "福田保税仓", "宝安机场仓"]),
            ("成都", 104.0668, 30.5728, ["高新西区仓", "锦江配送", "双流物流"]),
            ("武汉", 114.3054, 30.5931, ["汉口分拨", "武昌中转"]),
            ("西安", 108.9398, 34.3416, ["雁塔配送", "未央物流"])
        ]
        
        depot_list = []
        for city, bx, by, districts in major_cities:
            for district in districts:
                # Add small random offset to base city coords
                dx = random.uniform(-0.05, 0.05)
                dy = random.uniform(-0.05, 0.05)
                depot = models.Depot(
                    name=f"{city}{district}",
                    address=f"{city}市某区{district}示范地址",
                    x=bx + dx,
                    y=by + dy
                )
                db.add(depot)
                depot_list.append((city, bx, by)) # Keep track for customer generation

        # 3. Seed Vehicles (Need 20+)
        print("Creating fleet...")
        vehicle_types = [
            ("重型卡车", 5000.0),
            ("冷链运输车", 3000.0),
            ("中型货车", 2000.0),
            ("厢式货车", 1000.0),
            ("小型面包车", 500.0),
            ("无人配送车", 100.0)
        ]
        
        for i in range(1, 41):  # Increased to ~40
            v_type = random.choice(vehicle_types)
            v = models.Vehicle(
                name=f"{v_type[0]} {i:03d}号",
                capacity=v_type[1]
            )
            db.add(v)

        # 4. Seed Products (Need 100+)
        print("Creating products...")
        base_products = ["电子芯片", "智能手机", "办公桌椅", "生鲜水果", "冷冻肉类", "图书资料", "医疗器械", "汽车配件", "建筑材料", "日用百货", "五金工具", "运动器材", "化妆品", "母婴用品", "宠物食品"]
        
        unique_names = set()
        count = 1
        while len(unique_names) < 150: # Increased to 150
            base = random.choice(base_products)
            p_name = f"{base}-{count:03d}"
            if p_name not in unique_names:
                p = models.Product(
                    name=p_name,
                    weight=round(random.uniform(0.1, 10.0), 2)
                )
                db.add(p)
                unique_names.add(p_name)
                count += 1
        
        db.flush() 
        products = db.query(models.Product).all()

        # 5. Seed Customers (Need ~60)
        print("Creating customers across cities...")
        last_names = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
        first_names = "伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清飞彬富顺信子杰涛昌成康"
        
        customers = []
        for i in range(1, 101): # Increased to 100
            name = random.choice(last_names) + "".join(random.sample(first_names, random.randint(1, 2)))
            
            # Pick a random city base to generate customer near a city
            city, bx, by = random.choice(depot_list) 
            dx = random.uniform(-0.15, 0.15)
            dy = random.uniform(-0.15, 0.15)
            
            c = models.Customer(
                name=f"{name} (客户)",
                address=f"{city}市某街道{i}号",
                x=bx + dx,
                y=by + dy
            )
            db.add(c)
        
        db.flush()
        customers = db.query(models.Customer).all()

        # 6. Seed Orders (Need ~60)
        print("Creating orders...")
        if not products or not customers:
            print("Error: Missing products or customers for orders.")
            return

        for _ in range(120): # Increased to 120
            customer = random.choice(customers)
            order = models.Order(
                customer_id=customer.id,
                status=models.OrderStatus.PENDING,
                demand=0
            )
            db.add(order)
            db.flush() 

            # Add items - Adjusted for realistic capacity (Max ~5 items * 5 qty * 10kg = 250kg)
            num_items = random.randint(1, 5)
            total_weight = 0
            for _ in range(num_items):
                prod = random.choice(products)
                qty = random.randint(1, 5)
                item = models.OrderProduct(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty
                )
                db.add(item)
                total_weight += prod.weight * qty
            
            order.demand = round(total_weight, 2)
        
        db.commit()
        print("Data seeding completed successfully (Nationwide Data)!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
