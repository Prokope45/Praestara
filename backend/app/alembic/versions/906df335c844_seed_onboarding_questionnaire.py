"""seed_onboarding_questionnaire

Revision ID: 906df335c844
Revises: 783d162ef1f3
Create Date: 2026-03-15 13:02:16.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import uuid


# revision identifiers, used by Alembic.
revision = '906df335c844'
down_revision = 'ea0ea4bbd5b4'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection for seeding data
    conn = op.get_bind()
    
    # Get the first superuser to be the creator of the questionnaire
    result = conn.execute(text("SELECT id FROM \"user\" WHERE is_superuser = true LIMIT 1"))
    superuser_row = result.fetchone()
    
    if superuser_row:
        superuser_id = superuser_row[0]
        
        # Create the Praestara Onboarding questionnaire template
        questionnaire_id = str(uuid.uuid4())
        conn.execute(
            text("""
                INSERT INTO questionnairetemplate (id, title, description, is_active, created_by_id, created_at, updated_at)
                VALUES (:id, :title, :description, :is_active, :created_by_id, NOW(), NOW())
            """),
            {
                "id": questionnaire_id,
                "title": "Praestara Onboarding",
                "description": "Values, self-concept, agency, regulation, and context baseline. About 12 to 18 minutes.",
                "is_active": True,
                "created_by_id": superuser_id
            }
        )
        
        sections = [
            {"name": "Section A - Values and direction", "description": "Values and direction (text questions + likert)", "order": 0, "questions": [
                {"text": "In your own words, what feels most worth building, protecting, or moving toward in your life right now", "order": 0, "scale_type": "TEXT"},
                {"text": "When you feel most like yourself, what are you usually doing", "order": 1, "scale_type": "TEXT"},
                {"text": "What do you tend to regret not doing more than doing", "order": 2, "scale_type": "TEXT"},
                {"text": "I can name a few things that matter to me at a deep level", "order": 3, "scale_type": "LIKERT_5"},
                {"text": "I feel pulled between short-term comfort and long-term meaning", "order": 4, "scale_type": "LIKERT_5"},
                {"text": "My days feel connected to something larger than immediate demands", "order": 5, "scale_type": "LIKERT_5"},
                {"text": "Even when life is hard, I can usually tell what direction I want to move", "order": 6, "scale_type": "LIKERT_5"},
                {"text": "I often lose touch with what matters when I am stressed or tired", "order": 7, "scale_type": "LIKERT_5"},
                {"text": "I frequently feel uncertain about what I really care about", "order": 8, "scale_type": "LIKERT_5"},
            ]},
            {"name": "Section B - Valued living across domains", "description": "Valued living across domains (10 domain ratings)", "order": 1, "questions": [
                {"text": "Health and body care", "order": 9, "scale_type": "DOMAIN_RATING"},
                {"text": "Sleep and recovery", "order": 10, "scale_type": "DOMAIN_RATING"},
                {"text": "Work or contribution", "order": 11, "scale_type": "DOMAIN_RATING"},
                {"text": "Learning or skill building", "order": 12, "scale_type": "DOMAIN_RATING"},
                {"text": "Relationships and friendships", "order": 13, "scale_type": "DOMAIN_RATING"},
                {"text": "Family or close bonds", "order": 14, "scale_type": "DOMAIN_RATING"},
                {"text": "Community or service", "order": 15, "scale_type": "DOMAIN_RATING"},
                {"text": "Spiritual or existential life (if relevant)", "order": 16, "scale_type": "DOMAIN_RATING"},
                {"text": "Play, rest, enjoyment", "order": 17, "scale_type": "DOMAIN_RATING"},
                {"text": "Order, responsibility, life maintenance", "order": 18, "scale_type": "DOMAIN_RATING"},
            ]},
            {"name": "Section C - Self-concept clarity", "description": "", "order": 2, "questions": [
                {"text": "My sense of who I am feels consistent across different situations", "order": 19, "scale_type": "LIKERT_5"},
                {"text": "I feel like I understand myself fairly well", "order": 20, "scale_type": "LIKERT_5"},
                {"text": "My values and priorities feel stable enough to guide my decisions", "order": 21, "scale_type": "LIKERT_5"},
                {"text": "My sense of self changes drastically depending on who I am around", "order": 22, "scale_type": "LIKERT_5"},
                {"text": "I feel uncertain about who I really am", "order": 23, "scale_type": "LIKERT_5"},
                {"text": "I can imagine the kind of person I want to become in the future", "order": 24, "scale_type": "LIKERT_5"},
                {"text": "Stress makes it hard for me to recognize myself in my choices", "order": 25, "scale_type": "LIKERT_5"},
                {"text": "I feel like I am becoming someone over time, not just reacting to events", "order": 26, "scale_type": "LIKERT_5"},
                {"text": "I have a clear sense of what kind of person I do not want to become", "order": 27, "scale_type": "LIKERT_5"},
                {"text": "In a few sentences, describe the kind of person you are trying to become", "order": 28, "scale_type": "TEXT"},
            ]},
            {"name": "Section D - Agency and self-efficacy", "description": "", "order": 3, "questions": [
                {"text": "My actions make a real difference in my life", "order": 29, "scale_type": "LIKERT_5"},
                {"text": "I can take small steps that compound over time", "order": 30, "scale_type": "LIKERT_5"},
                {"text": "When I decide something matters, I can usually act on it", "order": 31, "scale_type": "LIKERT_5"},
                {"text": "I often feel stuck even when I want to change", "order": 32, "scale_type": "LIKERT_5"},
                {"text": "I tend to give up quickly when I do not see results", "order": 33, "scale_type": "LIKERT_5"},
                {"text": "I can recover from setbacks without abandoning my direction", "order": 34, "scale_type": "LIKERT_5"},
                {"text": "I rely on external pressure to do what I intend", "order": 35, "scale_type": "LIKERT_5"},
                {"text": "I trust myself to follow through on what I say matters", "order": 36, "scale_type": "LIKERT_5"},
            ]},
            {"name": "Section E - Motivation style", "description": "", "order": 4, "questions": [
                {"text": "I move toward challenges that matter to me", "order": 37, "scale_type": "LIKERT_5"},
                {"text": "I avoid tasks mainly because they feel emotionally uncomfortable", "order": 38, "scale_type": "LIKERT_5"},
                {"text": "Once I start something meaningful, it is easier to keep going", "order": 39, "scale_type": "LIKERT_5"},
                {"text": "I delay important things because the feelings around them are intense", "order": 40, "scale_type": "LIKERT_5"},
                {"text": "I do best when goals feel self-chosen rather than imposed", "order": 41, "scale_type": "LIKERT_5"},
                {"text": "I do best when someone else is expecting me to follow through", "order": 42, "scale_type": "LIKERT_5"},
                {"text": "I tend to seek immediate relief when I am stressed", "order": 43, "scale_type": "LIKERT_5"},
                {"text": "I can tolerate discomfort if it serves something I care about", "order": 44, "scale_type": "LIKERT_5"},
            ]},
            {"name": "Section F - Emotion regulation and reflection", "description": "", "order": 5, "questions": [
                {"text": "I can usually identify what I am feeling in the moment", "order": 45, "scale_type": "LIKERT_5"},
                {"text": "My emotions are often confusing or hard to name", "order": 46, "scale_type": "LIKERT_5"},
                {"text": "Strong emotions make it hard for me to think clearly", "order": 47, "scale_type": "LIKERT_5"},
                {"text": "When upset, I can return to baseline relatively quickly", "order": 48, "scale_type": "LIKERT_5"},
                {"text": "I judge myself harshly when I fall short of my intentions", "order": 49, "scale_type": "LIKERT_5"},
                {"text": "I can reflect on a difficult day without spiraling", "order": 50, "scale_type": "LIKERT_5"},
                {"text": "I tend to get stuck in thoughts instead of learning from them", "order": 51, "scale_type": "LIKERT_5"},
                {"text": "I can notice urges without acting on them immediately", "order": 52, "scale_type": "LIKERT_5"},
                {"text": "When you are under stress, what tends to help you return to yourself", "order": 53, "scale_type": "TEXT"},
            ]},
            {"name": "Section G - Current context and symptom burden", "description": "Current context and symptom burden (frequency scales)", "order": 6, "questions": [
                {"text": "Low interest or reduced pleasure", "order": 54, "scale_type": "FREQUENCY"},
                {"text": "Low mood or feeling down", "order": 55, "scale_type": "FREQUENCY"},
                {"text": "Low energy or fatigue", "order": 56, "scale_type": "FREQUENCY"},
                {"text": "Sleep disturbance (too little or too much)", "order": 57, "scale_type": "FREQUENCY"},
                {"text": "Appetite change (less or more)", "order": 58, "scale_type": "FREQUENCY"},
                {"text": "Feeling bad about yourself or like you are failing", "order": 59, "scale_type": "FREQUENCY"},
                {"text": "Trouble concentrating", "order": 60, "scale_type": "FREQUENCY"},
                {"text": "Moving or speaking slower than usual, or feeling very restless", "order": 61, "scale_type": "FREQUENCY"},
                {"text": "Feeling nervous or on edge", "order": 62, "scale_type": "FREQUENCY"},
                {"text": "Not being able to stop worrying", "order": 63, "scale_type": "FREQUENCY"},
                {"text": "Worrying too much about different things", "order": 64, "scale_type": "FREQUENCY"},
                {"text": "Trouble relaxing", "order": 65, "scale_type": "FREQUENCY"},
                {"text": "Being easily irritated", "order": 66, "scale_type": "FREQUENCY"},
                {"text": "Feeling afraid something bad will happen", "order": 67, "scale_type": "FREQUENCY"},
                {"text": "Restlessness that makes it hard to sit still", "order": 68, "scale_type": "FREQUENCY"},
            ]},
            {"name": "Section H - Consent-bounded use and preferences", "description": "", "order": 7, "questions": [
                {"text": "I want the system to be minimally talkative and mostly store my writing", "order": 69, "scale_type": "LIKERT_5"},
                {"text": "I want the system to occasionally ask probing questions when it notices imbalance", "order": 70, "scale_type": "LIKERT_5"},
                {"text": "I prefer the system to ask about domains I did not mention in my writing", "order": 71, "scale_type": "LIKERT_5"},
                {"text": "I want the system to focus on patterns over time rather than day-to-day evaluation", "order": 72, "scale_type": "LIKERT_5"},
                {"text": "I want the system to avoid advice and stick to reflection prompts", "order": 73, "scale_type": "LIKERT_5"},
                {"text": "I want to be able to export or delete my data at any time", "order": 74, "scale_type": "LIKERT_5"},
                {"text": "What are your overall thoughts and feelings about this program", "order": 75, "scale_type": "TEXT"},
                {"text": "What would make this system feel supportive rather than intrusive", "order": 76, "scale_type": "TEXT"},
            ]}
        ]
        
        # Insert all sections and questions
        for section in sections:
            section_id = str(uuid.uuid4())
            conn.execute(
                text("""
                    INSERT INTO questionsection (id, questionnaire_id, name, description, "order")
                    VALUES (:id, :questionnaire_id, :name, :description, :order)
                """),
                {
                    "id": section_id,
                    "questionnaire_id": questionnaire_id,
                    "name": section["name"],
                    "description": section["description"],
                    "order": section["order"]
                }
            )
            for question in section["questions"]:
                question_id = str(uuid.uuid4())
                conn.execute(
                    text("""
                        INSERT INTO question (id, questionnaire_id, section_id, question_text, "order", is_required, scale_type, custom_min_value, custom_max_value, custom_unit_label)
                        VALUES (:id, :questionnaire_id, :section_id, :question_text, :order, :is_required, :scale_type, :custom_min_value, :custom_max_value, :custom_unit_label)
                    """),
                    {
                        "id": question_id,
                        "questionnaire_id": questionnaire_id,
                        "section_id": section_id,
                        "question_text": question["text"],
                        "order": question["order"],
                        "is_required": True,
                        "scale_type": question["scale_type"],
                        "custom_min_value": None,
                        "custom_max_value": None,
                        "custom_unit_label": None
                    }
                )


def downgrade():
    # Remove the Praestara Onboarding questionnaire
    conn = op.get_bind()
    conn.execute(
        text("DELETE FROM questionnairetemplate WHERE title = 'Praestara Onboarding'")
    )
