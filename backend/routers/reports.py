from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import io

from database import get_db
from utils.auth import get_current_active_user
from services.report_service import ReportService

router = APIRouter()

@router.get("/daily")
async def get_daily_report(
    date: Optional[datetime] = None,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily report"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if date is None:
        date = datetime.now().date()
    
    report_service = ReportService(db)
    report_data = report_service.generate_daily_report(date)
    
    if format.lower() == "excel":
        # Generate Excel report
        output = report_service.generate_excel_report(report_data, "daily")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=daily_report_{date}.xlsx"}
        )
    else:
        # Generate PDF report (default)
        output = report_service.generate_pdf_report(report_data, "daily")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=daily_report_{date}.pdf"}
        )

@router.get("/weekly")
async def get_weekly_report(
    start_date: Optional[datetime] = None,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get weekly report"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if start_date is None:
        # Start from last Monday
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())
    
    report_service = ReportService(db)
    report_data = report_service.generate_weekly_report(start_date)
    
    if format.lower() == "excel":
        output = report_service.generate_excel_report(report_data, "weekly")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=weekly_report_{start_date}.xlsx"}
        )
    else:
        output = report_service.generate_pdf_report(report_data, "weekly")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=weekly_report_{start_date}.pdf"}
        )

@router.get("/monthly")
async def get_monthly_report(
    year: int,
    month: int,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get monthly report"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    report_service = ReportService(db)
    report_data = report_service.generate_monthly_report(year, month)
    
    if format.lower() == "excel":
        output = report_service.generate_excel_report(report_data, "monthly")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=monthly_report_{year}_{month:02d}.xlsx"}
        )
    else:
        output = report_service.generate_pdf_report(report_data, "monthly")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=monthly_report_{year}_{month:02d}.pdf"}
        )

@router.get("/stats")
async def get_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get system statistics"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    report_service = ReportService(db)
    stats = report_service.get_statistics(days)
    return stats