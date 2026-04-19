import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc

from app.api.deps import CurrentUser, SessionDep
from app.koios_client.KoiosClient import ai_client
from app.models import (
    Message,
    Trajectory,
    TrajectoryCreate,
    TrajectoryPublic,
    TrajectoriesPublic,
    TrajectoryUpdate,
)

router = APIRouter()


@router.get("/active", response_model=TrajectoriesPublic)
def get_active_trajectories(
    session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get active trajectories for the current user.
    """
    statement = (
        select(Trajectory)
        .where(
            Trajectory.user_id == current_user.id,
            Trajectory.is_active == True
        )
        .order_by(desc(Trajectory.created_at))
    )
    trajectories = session.exec(statement).all()
    return TrajectoriesPublic(data=trajectories, count=len(trajectories))


@router.get("/", response_model=TrajectoriesPublic)
def get_all_trajectories(
    session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get all trajectories (active and inactive) for the current user.
    """
    statement = (
        select(Trajectory)
        .where(Trajectory.user_id == current_user.id)
        .order_by(desc(Trajectory.created_at))
    )
    trajectories = session.exec(statement).all()
    return TrajectoriesPublic(data=trajectories, count=len(trajectories))


@router.post("/", response_model=TrajectoryPublic)
def create_trajectory(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    trajectory_in: TrajectoryCreate,
) -> Any:
    """
    Create a new trajectory goal. This will call the AI client to generate the yes/no question.
    """
    try:
        rephrased = ai_client.rephrase_trajectory_goal(str(current_user.id), trajectory_in.original_goal)
    except Exception as e:
        # Fallback to a generic rephrase if AI fails
        rephrased = f"Did you work on: {trajectory_in.original_goal}?"
        
    trajectory = Trajectory.model_validate(
        trajectory_in, 
        update={
            "user_id": current_user.id,
            "rephrased_question": rephrased
        }
    )
    session.add(trajectory)
    session.commit()
    session.refresh(trajectory)
    return trajectory


@router.patch("/{id}", response_model=TrajectoryPublic)
def update_trajectory(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    trajectory_in: TrajectoryUpdate,
) -> Any:
    """
    Update a trajectory goal.
    """
    trajectory = session.get(Trajectory, id)
    if not trajectory:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    if trajectory.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
        
    update_data = trajectory_in.model_dump(exclude_unset=True)
    
    # If the user changed the original goal, we should rephrase it
    if "original_goal" in update_data and update_data["original_goal"] != trajectory.original_goal:
        try:
            rephrased = ai_client.rephrase_trajectory_goal(str(current_user.id), update_data["original_goal"])
            update_data["rephrased_question"] = rephrased
        except Exception as e:
            update_data["rephrased_question"] = f"Did you work on: {update_data['original_goal']}?"
            
    trajectory.sqlmodel_update(update_data)
    session.add(trajectory)
    session.commit()
    session.refresh(trajectory)
    return trajectory


@router.delete("/{id}", response_model=Message)
def delete_trajectory(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """
    Delete a trajectory goal.
    """
    trajectory = session.get(Trajectory, id)
    if not trajectory:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    if trajectory.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    session.delete(trajectory)
    session.commit()
    return Message(message="Trajectory deleted successfully")


from pydantic import BaseModel

class BrainstormRequest(BaseModel):
    message: str

class BrainstormResponse(BaseModel):
    response: str


@router.post("/brainstorm", response_model=BrainstormResponse)
def brainstorm_trajectory(
    *,
    current_user: CurrentUser,
    request: BrainstormRequest,
) -> Any:
    """
    Brainstorm trajectory goals with Koios AI.
    """
    try:
        reply = ai_client.brainstorm_trajectory(str(current_user.id), request.message)
        return BrainstormResponse(response=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error communicating with AI service")
