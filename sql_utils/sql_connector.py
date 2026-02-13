import pymysql
from typing import List, Optional, Any, Dict
from dataclasses import dataclass, asdict

@dataclass
class BasketballCourt:
    id: Optional[int] = None
    name: str = ''
    description: str = ''
    operator: Optional[str] = None
    is_free: int = 0
    access_type: str = ''
    province: str = ''
    city: str = ''
    district: str = ''
    address: Optional[str] = None
    place_id: Optional[str] = None
    latitude: Optional[float] = None
    longtitude: Optional[float] = None
    nearest_transit: Optional[str] = None
    has_parking: Optional[int] = None
    free_parking: Optional[int] = None
    parking_type: Optional[str] = None
    parking_fee_info: Optional[str] = None
    parking_capacity: Optional[int] = None
    has_lights: Optional[int] = None
    light_type: Optional[str] = None
    light_hours_desc: Optional[str] = None
    surface_type: Optional[str] = None
    surface_notes: Optional[str] = None
    total_units_count: Optional[int] = None
    half_units_count: Optional[int] = None
    week_open_hours: Optional[str] = None
    free_open_hours: Optional[str] = None
    week_appointment_hours: Optional[str] = None
    appointment_type_desc: Optional[str] = None
    amenities_summary: Optional[str] = None
    gmt_create: Optional[str] = None
    creator: Optional[str] = None
    creator_id: Optional[str] = None
    gmt_modified: Optional[str] = None
    modifier_id: Optional[str] = None
    modifier: Optional[str] = None
    built_time: Optional[str] = None

@dataclass
class CourtUnit:
    id: Optional[int] = None
    court_id: int = 0
    unit_name: Optional[str] = None
    unit_type: str = ''
    length_m: Optional[int] = None
    width_m: Optional[int] = None
    is_standard: Optional[int] = None
    fenced: Optional[int] = None
    lines_painted: Optional[int] = None
    surface_condition_score: Optional[int] = None
    hoop_brand: Optional[str] = None
    hoop_material: Optional[str] = None
    rim_type: Optional[str] = None
    rim_height_cm: Optional[int] = None
    is_standard_rim: Optional[int] = None
    unit_status: Optional[str] = None
    gmt_create: Optional[str] = None
    gmt_modified: Optional[str] = None
    modifier_id: Optional[str] = None
    modifier: Optional[str] = None
    creator_id: Optional[str] = None
    creator: Optional[str] = None
    surface_type: Optional[str] = None
    surface_status: Optional[str] = None

class SqlConnector:
    def __init__(self):
        self.conn = pymysql.connect(host='rm-bp156i07744k1d1th1o.mysql.rds.aliyuncs.com', 
                                    port=3306, 
                                    user='test_dbuser', 
                                    passwd='tZ7mpuAQuq@yDYN', 
                                    db='main_db', 
                                    charset='utf8', 
                                    cursorclass=pymysql.cursors.DictCursor)

    def close(self):
        self.conn.close()

    # --- BasketballCourt CRUD ---
    def insert_basketball_court(self, court: BasketballCourt) -> int:
        with self.conn.cursor() as cursor:
            fields = [k for k, v in asdict(court).items() if v is not None and v != '' and k != 'id']
            values = [getattr(court, k) for k in fields]
            sql = f"INSERT INTO basketball_courts ({', '.join(fields)}) VALUES ({', '.join(['%s']*len(values))})"
            cursor.execute(sql, values)
            self.conn.commit()
            return cursor.lastrowid

    def get_basketball_court(self, court_id: int) -> Optional[BasketballCourt]:
        with self.conn.cursor() as cursor:
            sql = "SELECT * FROM basketball_courts WHERE id=%s"
            cursor.execute(sql, (court_id,))
            row = cursor.fetchone()
            return BasketballCourt(**row) if row else None

    def update_basketball_court(self, court: BasketballCourt) -> bool:
        with self.conn.cursor() as cursor:
            fields = [k for k, v in asdict(court).items() if v is not None and v != '' and k != 'id']
            values = [getattr(court, k) for k in fields]
            if not fields:
                return False
            sql = f"UPDATE basketball_courts SET {', '.join([f'{k}=%s' for k in fields])} WHERE id=%s"
            cursor.execute(sql, values + [court.id])
            self.conn.commit()
            return cursor.rowcount > 0

    def delete_basketball_court(self, court_id: int) -> bool:
        with self.conn.cursor() as cursor:
            sql = "DELETE FROM basketball_courts WHERE id=%s"
            cursor.execute(sql, (court_id,))
            self.conn.commit()
            return cursor.rowcount > 0

    def list_basketball_courts(self, where: str = '', params: List[Any] = []) -> List[BasketballCourt]:
        with self.conn.cursor() as cursor:
            sql = "SELECT * FROM basketball_courts"
            if where:
                sql += f" WHERE {where}"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [BasketballCourt(**row) for row in rows]

    def get_basketball_court_by_location(self, name: str, province: str, city: str, district: str) -> Optional[BasketballCourt]:
        """
        根据名称、省、市、区/县查询是否存在该球场
        """
        with self.conn.cursor() as cursor:
            sql = "SELECT * FROM basketball_courts WHERE name=%s AND province=%s AND city=%s AND district=%s LIMIT 1"
            cursor.execute(sql, (name, province, city, district))
            row = cursor.fetchone()
            return BasketballCourt(**row) if row else None

    # --- CourtUnit CRUD ---
    def insert_court_unit(self, unit: CourtUnit) -> int:
        with self.conn.cursor() as cursor:
            fields = [k for k, v in asdict(unit).items() if v is not None and v != '' and k != 'id']
            values = [getattr(unit, k) for k in fields]
            sql = f"INSERT INTO court_units ({', '.join(fields)}) VALUES ({', '.join(['%s']*len(values))})"
            cursor.execute(sql, values)
            self.conn.commit()
            return cursor.lastrowid

    def get_court_unit(self, unit_id: int) -> Optional[CourtUnit]:
        with self.conn.cursor() as cursor:
            sql = "SELECT * FROM court_units WHERE id=%s"
            cursor.execute(sql, (unit_id,))
            row = cursor.fetchone()
            return CourtUnit(**row) if row else None

    def update_court_unit(self, unit: CourtUnit) -> bool:
        with self.conn.cursor() as cursor:
            fields = [k for k, v in asdict(unit).items() if v is not None and v != '' and k != 'id']
            values = [getattr(unit, k) for k in fields]
            if not fields:
                return False
            sql = f"UPDATE court_units SET {', '.join([f'{k}=%s' for k in fields])} WHERE id=%s"
            cursor.execute(sql, values + [unit.id])
            self.conn.commit()
            return cursor.rowcount > 0

    def delete_court_unit(self, unit_id: int) -> bool:
        with self.conn.cursor() as cursor:
            sql = "DELETE FROM court_units WHERE id=%s"
            cursor.execute(sql, (unit_id,))
            self.conn.commit()
            return cursor.rowcount > 0

    def list_court_units(self, where: str = '', params: List[Any] = []) -> List[CourtUnit]:
        with self.conn.cursor() as cursor:
            sql = "SELECT * FROM court_units"
            if where:
                sql += f" WHERE {where}"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [CourtUnit(**row) for row in rows]