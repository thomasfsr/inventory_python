from pydantic import BaseModel, Field
from enum import Enum

class TaskOptions(Enum):
    CHATTING = 'chatting'
    UPDATE = 'update'
    QUERY = 'query'

class TaskModel(BaseModel):
    label: TaskOptions
    task: str

class ListTaskModel(BaseModel):
    task_list: list[TaskModel]

class ActionOptions(str,Enum):
    ADD = 'add'
    SUBTRACT = 'subtract'
    DISCARD_ALL = 'discard_all'
    RENAME = 'rename'
    CHANGE_UNIT = 'change_unit'

class UnitOptions(Enum):
    UNIDADES = "un"

    # Metric Units
    GRAMAS = "g"
    KILOGRAMAS = "kg"
    METROS = "m"
    CENTIMETROS = "cm"
    MILIMETROS = "mm"
    LITROS = "l"
    MILILITROS = "ml"
    METROS_QUADRADOS = "m2"
    METROS_CUBICOS = "m3"

    # US Customary Units
    POUND = "lb"
    OUNCE = "oz"
    INCH = "in"
    FOOT = "ft"
    YARD = "yd"
    MILE = "mi"
    GALLON = "gal"
    QUART = "qt"
    PINT = "pt"
    CUP = "cup"
    TEASPOON = "tsp"
    TABLESPOON = "tbsp"

    # Other Units
    PEDACO = "pcs"
    DUZIA = "duz"
    CASE = "case"
    PALLET = "pallet"
    ROLO = "rol"
    CAIXA = "cx"
    SACO = "saco"
    CARTON = "carton"
    FOLHA = "folha"
    PACOTE = "pct"

class FilteredTaskBaseModel(BaseModel):
    task_status: TaskOptions = Field(description='Whether the task is a update of the database or retrieve information from the database (query).')
    task: str = Field(description='The task itself')

class SQLQueryBaseModel(BaseModel):
    query: str = Field(description='The SQL analytical query')
class ListOfTasksBaseModel(BaseModel):
    tasks:list[FilteredTaskBaseModel]= Field(description='''The list of tasks identified.''')

class UpdateBaseModel(BaseModel):
    action: None | ActionOptions = Field(description='Action required for the task: add, subtract, discard')
    item_name: str = Field(description='Item of the task')
    quantity: None | float | int = Field(description='Quantity of the item in the task')
    unit: UnitOptions = Field(description='unit of the items quantity.')
    old_item_name:  str | None 
    new_item_name:  str | None 
    category: str | None = Field(description='Category of the item')
    description: str | None = Field(description='Description of the item')
    location: str | None = Field(description='Location of the item')
