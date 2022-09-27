import typing
from dataclasses import dataclass
from collections import OrderedDict

@dataclass(frozen=True)
class Request:
    scope: typing.Mapping[str, typing.Any]

    receive: typing.Callable[[], typing.Awaitable[object]]
    send: typing.Callable[[object], typing.Awaitable[None]]


class RestaurantManager:
    def __init__(self):
        self._staff = OrderedDict()
    
    @property
    def staff(self):
        return dict(self._staff)
    

    async def __call__(self, request: Request):
        request_type = request.scope["type"]
        request_id = request.scope.get("id")
        request_speciality = request.scope.get("speciality")

        if request_type == "staff.onduty":
            self._staff[request_id] = request

        if request_type == "staff.offduty":
            del self._staff[request_id]

        if request_type == "order":
            found = next(
                staff_request
                for staff_request in self._staff.values()
                if request_speciality in staff_request.scope["speciality"]
            )
            self._staff.move_to_end(found.scope["id"])

            full_order = await request.receive()
            await found.send(full_order)

            result = await found.receive()
            await request.send(result)