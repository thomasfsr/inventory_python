import httpx
from datetime import datetime, timezone
import jwt

BACKEND_URL = "http://127.0.0.1:8000"

async def login(username: str, password: str):
    """
    Send a POST request to the FastAPI backend to authenticate the user.
    """
    url = f"{BACKEND_URL}/auth/token"
    data = {
        "username": username, 
        "password": password
        }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        return "Nome ou/e Senha incorretos."
    elif response.status_code >= 500:
        return "Server error. Please try again later."
    else:
        return "An error occurred. Please try again."


async def add_item(token: str, item_data: dict):
    """
    Send a POST request to the FastAPI backend to add a new item.
    """
    url = f"{BACKEND_URL}/items/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=item_data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Failed to add item: {response.text}"

async def get_items(token: str):
    url = f"{BACKEND_URL}/items/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Falha em carregar seus items.{token}"

async def patch_item_request(token: str, item_id: int, item_data: dict):
    """
    Send a PATCH request to update an item in the inventory.
    """
    url = f"{BACKEND_URL}/items/{item_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(url, json=item_data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to update item: {response.text}"}

async def delete_item_request(token: str, item_id: int):
    url = f"{BACKEND_URL}/items/{item_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to delete item: {response.text}"}

column_map = {
    'quantity': 'quantidade',
    'name': 'nome',
    'unit': 'unidade de medida',
    'description': 'descrição',
    "location": "localização",
    "created_at": "data_criação",
    "updated_at": "data_atualização"
}
reverse_column_map = {v: k for k, v in column_map.items()}

async def update_database(token: str, **kwargs):
    new_items = kwargs.get("new_items", [])
    del_items = kwargs.get("del_items", [])
    change_map = kwargs.get("change_map", {})

    resp = []

    if change_map:
        for i in range(len(change_map['id'])):
            item_id = change_map['id'][i]
            column = change_map['column'][i]
            column = reverse_column_map.get(column, column)
            value = change_map['value'][i]
            
            resp.append(await patch_item_request(token=token, item_id=item_id, item_data={column: value}))
    
    if new_items:
        for item_data in new_items:
            item_data.pop("index", None)
            item_data.pop("deletar item?", None)
            resp.append(await add_item(token=token, item_data=item_data))
    
    if del_items:
        for item_id in del_items:
            resp.append(await delete_item_request(token=token, item_id=item_id))
    
    return resp