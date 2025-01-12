import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src import database as db
from sqlalchemy import *
from src.api import business_logic as bl

router = APIRouter()


class GoalJson(BaseModel):
    user_id: int
    type_id: int
    target_weight: int


@router.post("/goals/", tags=["goals"])
def create_goal(goal: GoalJson):  # 1
    with db.engine.begin() as conn:
        if goal.type_id != 0:
            raise HTTPException(status_code=400, detail="Invalid type_id")

        user = conn.execute(
            text(
                "SELECT starting_lbs, birthday, gender, height_inches FROM users WHERE id = :id"),
            {"id": goal.user_id}
        ).fetchone()

        try:
            distance_ft, times_per_week = bl.calculate_workout_plan(
                user, goal.target_weight)
        except ValueError as ve:
            return HTTPException(status_code=400, detail=str(ve))

        newWorkout = conn.execute(db.workouts.insert().values(
            workout_name="Run",
            weight=0,
            distance_ft=distance_ft,
            repetitions=None,
            seconds=None,
            sets=None,
            times_per_week=times_per_week,
            user_id=goal.user_id
        ))

        workout_id = newWorkout.inserted_primary_key[0]
        conn.execute(db.goals.insert().values(
            type_id=goal.type_id,
            user_id=goal.user_id,
            target_weight=goal.target_weight,
            workout_id=workout_id
        ))

    return {"message": "Goal created successfully."}
