import random
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models, auth

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

        # 2. Seed Depots (Need 10)
        print("Creating 10 depots...")
        shanghai_districts = [
            ("上海总仓", 121.4737, 31.2304), # Peopls Square
            ("浦东分拨中心", 121.5447, 31.2224),
            ("徐汇中转站", 121.4365, 31.1883),
            ("静安配送站", 121.4482, 31.2275),
            ("长宁物流中心", 121.4237, 31.2181),
            ("普陀分仓", 121.3925, 31.2492),
            ("虹口配送点", 121.4818, 31.2647),
            ("杨浦中转仓", 121.5255, 31.2595),
            ("闵行物流基地", 121.3816, 31.1128),
            ("宝山分拨站", 121.4896, 31.4053)
        ]
        
        for name, bx, by in shanghai_districts:
            depot = models.Depot(
                name=name,
                address=f"上海市{name[0:2]}区示范地址", # Simple demo address
                x=bx,
                y=by
            )
            db.add(depot)
        
        # 3. Seed Vehicles (Need 15+)
        print("Creating fleet...")
        vehicle_types = [
            ("重型卡车", 5000.0),
            ("轻型货车", 2000.0),
            ("厢式货车", 1000.0),
            ("小型面包车", 500.0),
            ("货运电动车", 100.0)
        ]
        
        for i in range(1, 21): 
            v_type = random.choice(vehicle_types)
            v = models.Vehicle(
                name=f"{v_type[0]} {i:03d}号",
                capacity=v_type[1]
            )
            db.add(v)

        # 4. Seed Products (Need 100+)
        print("Creating products...")
        base_products = ["电子配件", "办公桌椅", "生鲜食品", "图书资料", "医疗器械", "汽车配件", "建筑材料", "日用百货", "五金工具", "运动器材"]
        
        unique_names = set()
        count = 1
        while len(unique_names) < 120:
            base = random.choice(base_products)
            p_name = f"{base}-{count:03d}"
            if p_name not in unique_names:
                p = models.Product(
                    name=p_name,
                    weight=round(random.uniform(0.5, 50.0), 2)
                )
                db.add(p)
                unique_names.add(p_name)
                count += 1
        
        db.flush() # ensure IDs are generated
        products = db.query(models.Product).all()

        # 5. Seed Customers (Need ~50)
        print("Creating customers...")
        # Random Chinese names
        last_names = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
        first_names = "伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲江超浩亮政谦亨奇固之轮翰朗伯宏言若鸣朋斌梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄琛钧冠策腾楠榕风航弘"
        
        for i in range(1, 51):
            name = random.choice(last_names) + "".join(random.sample(first_names, random.randint(1, 2)))
            # Random offset around Shanghai
            dx = random.uniform(-0.1, 0.1)
            dy = random.uniform(-0.1, 0.1)
            c = models.Customer(
                name=f"{name} (客户)",
                address=f"上海市某街道{i}号",
                x=121.4737 + dx,
                y=31.2304 + dy
            )
            db.add(c)
        
        db.flush()
        customers = db.query(models.Customer).all()

        # 6. Seed Orders (Need ~60)
        print("Creating orders...")
        if not products or not customers:
            print("Error: Missing products or customers for orders.")
            return

        for _ in range(60):
            customer = random.choice(customers)
            order = models.Order(
                customer_id=customer.id,
                status=models.OrderStatus.PENDING,
                demand=0
            )
            db.add(order)
            db.flush() 

            # Add items
            num_items = random.randint(1, 8)
            total_weight = 0
            for _ in range(num_items):
                prod = random.choice(products)
                qty = random.randint(1, 20)
                item = models.OrderProduct(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty
                )
                db.add(item)
                total_weight += prod.weight * qty
            
            order.demand = round(total_weight, 2)
        
        db.commit()
        print("Data seeding completed successfully (Chinese localization)!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
