# src/services/ies_service.py
import psycopg2
from dataclasses import dataclass
from typing import List, Tuple, Optional
from config.conn import conectar

@dataclass
class IES:
    id: int
    entity_name: str
    entity_code: str
    api_key: str

def list_active() -> List[Tuple[int, str, str]]:
   
    sql = """
        SELECT id, entity_name, entity_code, api_key
        FROM ensalamento.tbConfigIes
        WHERE is_active = TRUE
        ORDER BY entity_name;
    """
    conn = conectar()
    if not conn:
        print("Falha ao conectar ao banco.")
        return []

    cur = None
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return [IES(id=row[0], entity_name=row[1], entity_code=row[2], api_key=row[3]) for row in rows]
    except Exception as e:
        print(f"Erro ao listar IES ativas: {type(e).__name__}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return []
    finally:
        if cur:
            cur.close()
        conn.close()

def get_by_id(ies_id: int) -> Optional[IES]:

    sql = """
        SELECT id, entity_name, entity_code, api_key
        FROM pensalamento.tbConfigIes
        WHERE id = %s AND is_active = TRUE;
    """
    conn = conectar()
    if not conn:
        print("Falha ao conectar ao banco.")
        return None

    cur = None
    try:
        cur = conn.cursor()
        cur.execute(sql, (ies_id,))
        row = cur.fetchone()
        if not row:
            return None
        return IES(*row)
    except Exception as e:
        print(f"Erro ao buscar IES id={ies_id}: {type(e).__name__}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        if cur:
            cur.close()
        conn.close()
