"""API request and response schemas."""
from typing import Dict, Optional
from pydantic import BaseModel


class NewTabRequest(BaseModel):
    """Request schema for creating a new tab."""
    url: str
    tab_name: str
    cookie: Optional[str] = None
    local_storage: Optional[Dict[str, str]] = None


class ClickRequest(BaseModel):
    """Request schema for clicking an element."""
    tab_name: str
    selector: str


class TabResponse(BaseModel):
    """Response schema for tab operations."""
    code: int
    message: str
    tab_name: str = None


class HTMLResponse(BaseModel):
    """Response schema for HTML content."""
    code: int
    tab_name: str
    html: str


class TabsListResponse(BaseModel):
    """Response schema for listing tabs."""
    tabs: list[str]
