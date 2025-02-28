from saur_client import (
    SaurResponseContracts,
    SaurResponseDelivery,
    SaurResponseLastKnow,
)

from .models import ClientId as ClientId
from .models import ContratId, RelevePhysique, SectionId, StrDate

class Compteur:
    sectionId: SectionId
    clientReference: str
    contractName: str
    clientId: ClientId
    contractId: ContratId
    isContractTerminated: bool
    date_installation: StrDate
    pairingTechnologyCode: str
    releve_physique: RelevePhysique
    manufacturer: str
    model: str
    serial_number: str
    def __init__(self, sectionId: SectionId, clientReference: str, clientId: ClientId, contractName: str, contractId: ContratId, isContractTerminated: bool, date_installation: StrDate, pairingTechnologyCode: str, releve_physique: RelevePhysique, manufacturer: str, model: str, serial_number: str) -> None: ...
    def update_delivery(self, delivery_response: SaurResponseDelivery) -> None: ...
    def update_last(self, last_response: SaurResponseLastKnow) -> None: ...

class Compteurs(list[Compteur]):
    pass

def extract_compteurs_from_area(area_response: SaurResponseContracts) -> Compteurs: ...

