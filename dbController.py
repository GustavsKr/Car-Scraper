from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    TIMESTAMP,
    DECIMAL,
    Boolean,
    func,
    desc,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from utils.logger import logger

Base = declarative_base()

class SsCars(Base):
    __tablename__ = "ss_cars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(255), nullable=False)
    img_url = Column(String(255))
    brand = Column(String(40), nullable=False)
    model = Column(String(50))
    price = Column(DECIMAL(10, 2), nullable=True)
    year = Column(Integer, nullable=True)
    volume = Column(DECIMAL(3, 1))
    engine_type = Column(
        Enum(
            'gasoline', 
            'diesel', 
            'electric', 
            'hybrid', 
            'naturalgas', 
            'lpg', 
            'ethanol', 
            'hydrogen', 
            name="engine_type_enum"
        ), 
        nullable=True  # Allow None
    )
    gearbox = Column(Enum('manual', 'automatic', name="gearbox_enum"), nullable=True)
    body_type = Column(
        Enum(
            'hatchback',
            'convertible', 
            'coupe/sportscar', 
            'suv/off-road/jeep', 
            'stationwagon/universal', 
            'sedan', 
            'van/minivan', 
            'pickup', 
            name="body_type_enum"
        ), 
        nullable=True  # Allow None
    )
    color = Column(
        Enum(
            "beige",
            "blue",
            "brown",
            "bronze",
            "yellow",
            "grey",
            "green",
            "red",
            "black",
            "silver",
            "pink",
            "white",
            "orange",
            "gold",
            "purple",
            "matte",
            name="color_enum"
        ), 
        nullable=True  # Allow None
    )
    area = Column(String(50))
    deal_type = Column(String(15))
    run = Column(Integer)
    checkup = Column(String(7))  # Format: MM.YYYY
    fetching_date = Column(TIMESTAMP, default=func.now())

class Auto24Cars(Base):
    __tablename__ = "auto24_cars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(255), nullable=False)
    img_url = Column(String(255))
    brand = Column(String(40), nullable=False)
    model = Column(String(50))
    price = Column(DECIMAL(10, 2), nullable=True)
    year = Column(Integer, nullable=True)
    volume = Column(DECIMAL(3, 1))
    engine_type = Column(
        Enum(
            'gasoline',
            'diesel',
            'electric',
            'hybrid',
            'naturalgas',
            'lpg',
            'ethanol',
            'hydrogen',
            name="engine_type_enum"
        ),
        nullable=True
    )
    gearbox = Column(Enum('manual', 'automatic', name="gearbox_enum"), nullable=True)
    body_type = Column(
        Enum(
            'hatchback',
            'convertible',
            'coupe/sportscar',
            'suv/off-road/jeep',
            'stationwagon/universal',
            'sedan',
            'van/minivan',
            'pickup',
            name="body_type_enum"
        ),
        nullable=True
    )
    color = Column(
        Enum(
            "beige",
            "blue",
            "brown",
            "bronze",
            "yellow",
            "grey",
            "green",
            "red",
            "black",
            "silver",
            "pink",
            "white",
            "orange",
            "gold",
            "purple",
            "matte",
            name="color_enum"
        ),
        nullable=True
    )
    area = Column(String(50))
    deal_type = Column(String(15))
    run = Column(Integer)
    checkup = Column(String(7))  # Format: MM.YYYY
    fetching_date = Column(TIMESTAMP, default=func.now())

class AutopliusCars(Base):
    __tablename__ = "autoplius_cars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(255), nullable=False)
    img_url = Column(String(255))
    brand = Column(String(40), nullable=False)
    model = Column(String(50))
    price = Column(DECIMAL(10, 2), nullable=True)
    year = Column(Integer, nullable=True)
    volume = Column(DECIMAL(3, 1))
    engine_type = Column(
        Enum(
            'gasoline',
            'diesel',
            'electric',
            'hybrid',
            'naturalgas',
            'lpg',
            'ethanol',
            'hydrogen',
            name="engine_type_enum"
        ),
        nullable=True
    )
    gearbox = Column(Enum('manual', 'automatic', name="gearbox_enum"), nullable=True)
    body_type = Column(
        Enum(
            'hatchback',
            'convertible',
            'coupe/sportscar',
            'suv/off-road/jeep',
            'stationwagon/universal',
            'sedan',
            'van/minivan',
            'pickup',
            name="body_type_enum"
        ),
        nullable=True
    )
    color = Column(
        Enum(
            "beige",
            "blue",
            "brown",
            "bronze",
            "yellow",
            "grey",
            "green",
            "red",
            "black",
            "silver",
            "pink",
            "white",
            "orange",
            "gold",
            "purple",
            "matte",
            name="color_enum"
        ),
        nullable=True
    )
    area = Column(String(50))
    deal_type = Column(String(15))
    run = Column(Integer)
    checkup = Column(String(7))  # Format: MM.YYYY
    fetching_date = Column(TIMESTAMP, default=func.now())


class DbController:
    def __init__(self, connection_string):
        self.engine = create_engine(
            connection_string
        )
        self.Session = sessionmaker(bind=self.engine)

    def add_to_cars_table(
        self, 
        table_name,  # Table name as a string, e.g., "ss_cars", "auto24_cars", etc.
        url,
        img_url,
        brand,
        model,
        price,
        year,
        volume,
        engine_type,
        gearbox,
        body_type,
        color,
        area,
        deal_type,
        run,
        checkup,
        fetching_date
    ) -> None:
        # Mapping of table names to classes
        table_mapping = {
            "ss_cars": SsCars,
            "auto24_cars": Auto24Cars,
            "autoplius_cars": AutopliusCars,
        }

        # Resolve the table class from the name
        table_class = table_mapping.get(table_name)
        if not table_class:
            logger.exception(f"Invalid table name: {table_name}")
            return

        session = self.Session()
        try:
            # Check the last 10 entries for duplicates
            recent_entries = session.query(table_class.url) \
                                .order_by(desc(table_class.id)) \
                                .limit(10) \
                                .all()
            
            recent_urls = {entry.url for entry in recent_entries}

            if url in recent_urls:
                logger.info(f"Duplicate entry found in the last 10 records: {url}")
                return  # Skip adding duplicate entry

            # Prepare data dynamically
            car_data = {
                "url": url,
                "img_url": img_url,
                "brand": brand,
                "model": model,
                "price": price,
                "year": year,
                "volume": volume,
                "engine_type": engine_type,
                "gearbox": gearbox,
                "body_type": body_type,
                "color": color,
                "area": area,
                "deal_type": deal_type,
                "run": run,
                "checkup": checkup,
                "fetching_date": fetching_date
            }

            new_transport = table_class(**car_data)

            session.add(new_transport)
            session.commit()

        except SQLAlchemyError as e:
            logger.exception(f"Error adding to {table_name}: {e}")
            session.rollback()
        finally:
            session.close()
        