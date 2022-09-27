import typing
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    scope: typing.Mapping[str, typing.Any]

    receive: typing.Callable[[], typing.Awaitable[object]]
    send: typing.Callable[[object], typing.Awaitable[None]]


class RestaurantManager:
    def __init__(self):
        """Instantiate the restaurant manager.

        This is called at the start of each day before any staff get on
        duty or any orders come in.
        """
        # Dictionary that holds all on-duty staff members 
        # Key: Staff ID
        # Value: On-duty request
        self.staff = {}

        # Dictionary that holds all specialities logged via on-duty requests 
        # Key: Speciality 
        # Value: List that holds staff ID of all people that have corresponding speciality
        self.specialities = {}

        # Dictionary that maps staff ID to speciality
        # Key: Staff ID
        # Value: Speciality
        self.index = {}

    async def __call__(self, request: Request):
        """Handle a request received.

        :param request: request object
            Request object containing information about the sent
            request to your application.
        """
        type = request.scope["type"]
        
        match type:
            case "staff.onduty":
                id = request.scope["id"]
                spec = request.scope["speciality"]

                self.staff[id] = request
                self.index[id] = spec

                # Checks type of speciality and stores it accordingly
                if isinstance(spec, str):
                    if spec in self.specialities:
                        self.specialities[spec].append(id)
                    else:
                        self.specialities[spec] = [id,]
                elif isinstance(spec, (list, tuple)):
                    for s in spec:
                        if s in self.specialities:
                            self.specialities[s].append(id)
                        else:
                            self.specialities[s] = [id,]
                else:
                    raise TypeError("Speciality is of undefined type.")

            case "staff.offduty":
                id = request.scope["id"]

                del self.staff[id]
            
                if isinstance(self.index[id], str):
                    self.specialities[self.index[id]].remove(id)
                elif isinstance(self.index[id], (list, tuple)):
                    for s in self.index[id]:
                        self.specialities[s].remove(id)
                else:
                    raise TypeError("Speciality is of undefined type.")
                        
                del self.index[id]

            case "order":
                spec = request.scope["speciality"]

                found = self.staff[self.specialities[spec][0]]

                # Move staff ID elements in list up to
                # maintain fair distribution of work
                temp = self.specialities[spec][0]
                size = len(self.specialities[spec]) - 1
                for i in range(size):
                    self.specialities[spec][i] = self.specialities[spec][i+1]
                self.specialities[spec][size] = temp
                
                full_order = await request.receive()
                await found.send(full_order)

                result = await found.receive()
                await request.send(result)