"""
Pydantic data validation schemas for Egypt phone prices pipeline.
Provides data validation for specs, prices, stores, and pipeline status.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator


class PhoneCondition(str, Enum):
    """Phone condition enumeration."""
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"


class StoreName(str, Enum):
    """Available store names."""
    EGYPT_PRICES = "egypt_prices"
    ORANGE = "orange"
    VODAFONE = "vodafone"
    ETISALAT = "etisalat"
    CLARO = "claro"
    JUMIA = "jumia"
    OTHER = "other"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SpecsValidator(BaseModel):
    """Validation schema for phone specifications."""
    
    phone_id: str = Field(..., min_length=1, description="Unique phone identifier")
    brand: str = Field(..., min_length=1, description="Phone brand/manufacturer")
    model: str = Field(..., min_length=1, description="Phone model name")
    release_date: Optional[str] = Field(None, description="Phone release date (YYYY-MM-DD)")
    os: Optional[str] = Field(None, description="Operating system (Android, iOS, etc.)")
    os_version: Optional[str] = Field(None, description="OS version")
    processor: Optional[str] = Field(None, description="CPU/Processor name")
    ram_gb: Optional[float] = Field(None, ge=0, description="RAM in GB")
    storage_gb: Optional[float] = Field(None, ge=0, description="Storage in GB")
    storage_expandable: Optional[bool] = Field(None, description="Whether storage is expandable")
    display_size_inch: Optional[float] = Field(None, ge=0, description="Display size in inches")
    display_type: Optional[str] = Field(None, description="Display technology (AMOLED, IPS, etc.)")
    display_refresh_rate: Optional[int] = Field(None, ge=0, description="Refresh rate in Hz")
    resolution: Optional[str] = Field(None, description="Screen resolution (e.g., 1080x2400)")
    battery_mah: Optional[int] = Field(None, ge=0, description="Battery capacity in mAh")
    charging_watts: Optional[float] = Field(None, ge=0, description="Fast charging wattage")
    rear_camera_mp: Optional[str] = Field(None, description="Rear camera megapixels")
    front_camera_mp: Optional[str] = Field(None, description="Front camera megapixels")
    network: Optional[List[str]] = Field(None, description="Supported networks (4G, 5G, etc.)")
    colors: Optional[List[str]] = Field(None, description="Available colors")
    weight_grams: Optional[float] = Field(None, ge=0, description="Weight in grams")
    dimensions: Optional[str] = Field(None, description="Dimensions (L x W x H mm)")
    ip_rating: Optional[str] = Field(None, description="IP rating for water/dust resistance")
    biometric: Optional[List[str]] = Field(None, description="Biometric authentication methods")
    additional_features: Optional[Dict[str, Any]] = Field(None, description="Additional specifications")
    
    class Config:
        use_enum_values = False


class PriceValidator(BaseModel):
    """Validation schema for phone prices."""
    
    phone_id: str = Field(..., min_length=1, description="Unique phone identifier")
    store: StoreName = Field(..., description="Store/retailer name")
    original_price: float = Field(..., gt=0, description="Original/list price in EGP")
    current_price: Optional[float] = Field(None, ge=0, description="Current selling price in EGP")
    discount_percent: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage")
    currency: str = Field(default="EGP", description="Currency code")
    condition: PhoneCondition = Field(default=PhoneCondition.NEW, description="Phone condition")
    storage_variant: Optional[str] = Field(None, description="Storage variant (e.g., 128GB, 256GB)")
    color_variant: Optional[str] = Field(None, description="Color variant")
    warranty_months: Optional[int] = Field(None, ge=0, description="Warranty period in months")
    in_stock: Optional[bool] = Field(None, description="Stock availability")
    availability_text: Optional[str] = Field(None, description="Custom availability message")
    price_url: Optional[str] = Field(None, description="URL to product page")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when price was scraped")
    
    @validator('current_price', always=True)
    def validate_current_price(cls, v, values):
        """Ensure current_price doesn't exceed original_price."""
        if v is not None and 'original_price' in values:
            if v > values['original_price']:
                raise ValueError('current_price cannot exceed original_price')
        return v
    
    @validator('discount_percent', always=True)
    def validate_discount(cls, v, values):
        """Validate discount percent matches original and current price."""
        if v is not None and 'original_price' in values and 'current_price' in values:
            if values['current_price'] is not None:
                calculated_discount = ((values['original_price'] - values['current_price']) / values['original_price']) * 100
                # Allow 1% tolerance for rounding errors
                if abs(v - calculated_discount) > 1:
                    raise ValueError(f'discount_percent ({v}%) does not match calculated discount ({calculated_discount:.2f}%)')
        return v
    
    class Config:
        use_enum_values = False


class StoreValidator(BaseModel):
    """Validation schema for store/retailer information."""
    
    store_id: str = Field(..., min_length=1, description="Unique store identifier")
    name: StoreName = Field(..., description="Store name")
    display_name: str = Field(..., min_length=1, description="Display name for the store")
    website: Optional[str] = Field(None, description="Store website URL")
    country: str = Field(default="Egypt", description="Country where store operates")
    city: Optional[str] = Field(None, description="Primary city of operation")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email")
    active: bool = Field(default=True, description="Whether store is active")
    scraper_enabled: bool = Field(default=True, description="Whether scraping is enabled for this store")
    scraper_type: Optional[str] = Field(None, description="Type of scraper (selenium, bs4, api, etc.)")
    last_scraped: Optional[datetime] = Field(None, description="Timestamp of last successful scrape")
    scrape_frequency_hours: Optional[int] = Field(None, ge=1, description="Scrape frequency in hours")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional store metadata")
    
    class Config:
        use_enum_values = False


class PipelineStatusValidator(BaseModel):
    """Validation schema for pipeline execution status."""
    
    pipeline_id: str = Field(..., min_length=1, description="Unique pipeline execution ID")
    status: PipelineStatus = Field(..., description="Current pipeline status")
    stage: str = Field(..., min_length=1, description="Current pipeline stage")
    start_time: datetime = Field(..., description="Pipeline start timestamp")
    end_time: Optional[datetime] = Field(None, description="Pipeline end timestamp")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Pipeline execution duration in seconds")
    total_phones_processed: Optional[int] = Field(None, ge=0, description="Total phones processed")
    total_prices_scraped: Optional[int] = Field(None, ge=0, description="Total prices scraped")
    total_specs_updated: Optional[int] = Field(None, ge=0, description="Total specs updated")
    stores_processed: Optional[List[str]] = Field(None, description="List of stores processed")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="List of errors encountered")
    warnings: Optional[List[str]] = Field(None, description="List of warnings")
    success_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Success rate as percentage")
    log_file: Optional[str] = Field(None, description="Path to pipeline log file")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional execution metadata")
    
    @root_validator
    def validate_timestamps(cls, values):
        """Validate that end_time is after start_time."""
        start = values.get('start_time')
        end = values.get('end_time')
        if start and end and end < start:
            raise ValueError('end_time must be after start_time')
        return values
    
    @validator('duration_seconds', always=True)
    def calculate_duration(cls, v, values):
        """Calculate duration from timestamps if not provided."""
        if v is None and 'start_time' in values and 'end_time' in values:
            start = values['start_time']
            end = values['end_time']
            if start and end:
                return (end - start).total_seconds()
        return v
    
    class Config:
        use_enum_values = False


class BulkPricesValidator(BaseModel):
    """Validation schema for bulk price updates."""
    
    prices: List[PriceValidator] = Field(..., min_items=1, description="List of price records")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    batch_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Batch creation timestamp")
    
    class Config:
        use_enum_values = False


class BulkSpecsValidator(BaseModel):
    """Validation schema for bulk specs updates."""
    
    specs: List[SpecsValidator] = Field(..., min_items=1, description="List of specification records")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    batch_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Batch creation timestamp")
    
    class Config:
        use_enum_values = False


class PhoneRecordValidator(BaseModel):
    """Validation schema for complete phone records (specs + prices)."""
    
    specs: SpecsValidator = Field(..., description="Phone specifications")
    prices: List[PriceValidator] = Field(default_factory=list, description="Phone prices from different stores")
    
    class Config:
        use_enum_values = False


class ValidationResultValidator(BaseModel):
    """Validation schema for validation results."""
    
    is_valid: bool = Field(..., description="Whether validation passed")
    record_type: str = Field(..., description="Type of record validated")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")
    
    class Config:
        use_enum_values = False
