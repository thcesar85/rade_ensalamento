from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ActivityPayload:
    entityCode: str
    courseCode: str
    groupCode: str
    place: str
    taskCode: str
    date: str
    startTime: str
    endTime: str
    students: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entityCode": self.entityCode,
            "courseCode": self.courseCode,
            "groupCode": self.groupCode,
            "place": self.place,
            "taskCode": self.taskCode,
            "date": self.date,
            "startTime": self.startTime,
            "endTime": self.endTime,
            "students": self.students,
        }


@dataclass
class SummaryRow:
    lobby_id: int
    entitycode: str
    course: str
    grupo: str
    cpf: str
    data: str
    hora: str
    status: str
    http: int
    mensagem: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lobby_id": self.lobby_id,
            "entitycode": self.entitycode,
            "course": self.course,
            "grupo": self.grupo,
            "cpf": self.cpf,
            "data": self.data,
            "hora": self.hora,
            "status": self.status,
            "http": self.http,
            "mensagem": self.mensagem,
        }
