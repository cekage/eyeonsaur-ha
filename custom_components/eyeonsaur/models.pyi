import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, NewType

if TYPE_CHECKING:
    from .device import Compteurs

StrDate = NewType("StrDate", str)

@dataclass(frozen=True, slots=True)
class ConsumptionData:
    startDate: StrDate
    value: float
    rangeType: str
    def __init__(
        self, startDate: StrDate, value: float, rangeType: str
    ) -> None: ...

@dataclass(frozen=True, slots=True)
class AnchorData:
    readingDate: StrDate
    indexValue: float
    def __init__(self, readingDate: StrDate, indexValue: float) -> None: ...

@dataclass(frozen=True, slots=True)
class TheoreticalConsumptionData:
    date: StrDate
    indexValue: float
    def __init__(self, date: StrDate, indexValue: float) -> None: ...

@dataclass(frozen=True, slots=True)
class MissingDate:
    year: int
    month: int
    day: int
    def __init__(self, year: int, month: int, day: int) -> None: ...

@dataclass(slots=True, frozen=True)
class RelevePhysique:
    date: StrDate
    valeur: float
    def __init__(self, date: StrDate, valeur: float) -> None: ...

class ContratId(str):
    pass

class SectionId(str):
    pass

class JsonStr(str):
    pass

SaurSqliteResponse = tuple[sqlite3.Row, ...] | None

TheoreticalConsumptionDatas = NewType(
    "TheoreticalConsumptionDatas", list[TheoreticalConsumptionData]
)
ConsumptionDatas = NewType("ConsumptionDatas", list[ConsumptionData])

MissingDates = NewType("MissingDates", list[MissingDate])

@dataclass(slots=True, frozen=True)
class Contract:
    contract_id: ContratId
    contract_name: str
    isContractTerminated: bool

    def __init__(
        self,
        contract_id: ContratId,
        contract_name: str,
        isContractTerminated: bool,
    ) -> None: ...

Contracts = NewType("Contracts", list[Contract])

ClientId = NewType("ClientId", str)

@dataclass(slots=True, frozen=True)
class SaurData:
    saurClientId: ClientId
    compteurs: Compteurs
    contracts: Contracts
    def __init__(
        self, saurClientId: ClientId, compteurs: Compteurs, contracts: Contracts
    ) -> None: ...
