from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberOut,
    WorkspaceOut,
)


router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


def get_accessible_workspace(
    workspace_id: int,
    db: Session,
    current_user: User,
) -> Workspace:
    workspace = (
        db.query(Workspace)
        .outerjoin(
            WorkspaceMember,
            WorkspaceMember.workspace_id == Workspace.id,
        )
        .filter(
            Workspace.id == workspace_id,
            or_(
                Workspace.owner_id == current_user.id,
                WorkspaceMember.user_id == current_user.id,
            ),
        )
        .first()
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return workspace


@router.post(
    "",
    response_model=WorkspaceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    workspace = Workspace(
        name=payload.name,
        owner_id=current_user.id,
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return workspace


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Workspace]:
    workspaces = (
        db.query(Workspace)
        .outerjoin(
            WorkspaceMember,
            WorkspaceMember.workspace_id == Workspace.id,
        )
        .filter(
            or_(
                Workspace.owner_id == current_user.id,
                WorkspaceMember.user_id == current_user.id,
            )
        )
        .distinct()
        .order_by(Workspace.id)
        .all()
    )

    return workspaces


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberOut],
)
def list_workspace_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkspaceMemberOut]:
    workspace = get_accessible_workspace(workspace_id, db, current_user)

    members = [
        WorkspaceMemberOut(
            user_id=workspace.owner.id,
            email=workspace.owner.email,
            full_name=workspace.owner.full_name,
            role="owner",
        )
    ]

    membership_rows = (
        db.query(WorkspaceMember)
        .join(User, User.id == WorkspaceMember.user_id)
        .filter(WorkspaceMember.workspace_id == workspace.id)
        .order_by(WorkspaceMember.id)
        .all()
    )

    members.extend(
        WorkspaceMemberOut(
            user_id=membership.user.id,
            email=membership.user.email,
            full_name=membership.user.full_name,
            role=membership.role,
        )
        for membership in membership_rows
    )

    return members


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberOut,
    status_code=status.HTTP_201_CREATED,
)
def add_workspace_member(
    workspace_id: int,
    payload: WorkspaceMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceMemberOut:
    workspace = (
        db.query(Workspace)
        .filter(
            Workspace.id == workspace_id,
            Workspace.owner_id == current_user.id,
        )
        .first()
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found or insufficient permissions",
        )

    user = db.query(User).filter(User.email == payload.email).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == workspace.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace owner is already a member",
        )

    existing_membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )

    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a workspace member",
        )

    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=payload.role,
    )

    db.add(membership)
    db.commit()
    db.refresh(membership)

    return WorkspaceMemberOut(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
    )


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    return get_accessible_workspace(workspace_id, db, current_user)
