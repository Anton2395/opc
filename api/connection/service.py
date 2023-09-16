from connection.models import Connection, Area, Value


def check_name_connection(name: str, id_connect: int) -> bool:
    connections = Connection.objects.filter(name=name)
    if id_connect:
        answer = True
        for connect in connections:
            if connect.id != id_connect:
                answer = False
        return not answer
    else:
        return not connections.exists()


def check_name_area(name: str, connection_id: int, area_id: int) -> bool:
    connection = Connection.objects.get(pk=connection_id)
    areas = connection.area.filter(name=name)
    if area_id:
        answer = True
        for area in areas:
            if area.id != area_id:
                answer = False
        return answer
    else:
        return not areas.exists()


def check_name_variable(name: str, area_id: int, variable_id: int) -> bool:
    area = Area.objects.get(pk=area_id)
    values = area.value.filter(name=name)
    if variable_id:
        answer = True
        for value in values:
            if value.id != variable_id:
                answer = False
        return answer
    else:
        return not values.exists()
