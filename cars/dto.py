from dataclasses import dataclass
from datetime import datetime
from django.contrib.gis.geos import Point
from typing import List, Optional, Tuple

@dataclass
class TrackPointRequestDTO:
    vehicle_id: int
    start_time: str
    end_time: str
    output_format: str

@dataclass
class TrackPointResponseDTO:
    data: dict

@dataclass
class TripSummaryRequestDTO:
    vehicle_id: int
    start_time: str
    end_time: str

@dataclass
class TripSummaryDTO:
    start_time_local: str
    end_time_local: str
    duration: Optional[str]
    start_location: Optional[List[float]]
    start_address: Optional[str]
    end_location: Optional[List[float]]
    end_address: Optional[str]

@dataclass
class VehicleDetailDTO:
    vehicle_id: int
    start_time: Optional[str]
    end_time: Optional[str]

@dataclass
class ReportRequestDTO:
    report_type: str
    vehicle_id: Optional[str]
    driver_id: Optional[str]
    enterprise_id: Optional[str]
    start_date: str
    end_date: str
    period: str

@dataclass
class TripUploadDTO:
    vehicle_id: int
    start_time: datetime
    end_time: datetime
    gpx_file: bytes