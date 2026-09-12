from typing import List


class ActionEngine:
    """
    Rule-based decision support system generating standard operational procedures (SOPs)
    for district disaster authorities with mandatory human-in-the-loop statutory disclaimers.
    """

    STATUTORY_DISCLAIMER = (
        "Operational decision-support recommendation. Final emergency command authority "
        "remains with authorized District Disaster Management Officers."
    )

    ACTION_PROTOCOLS = {
        "LOW": [
            "Maintain standard automated telemetry polling (15-min cycles).",
            "Verify all telemetry telemetry gateway links and battery backups.",
            "Log routine meteorological baseline observations.",
        ],
        "MODERATE": [
            "Increase gauge monitoring frequency to 5-minute telemetry intervals.",
            "Notify local Tehsil emergency response coordinators to standby.",
            "Broadcast precautionary advisory to low-lying riverside communities.",
            "Verify emergency HF/VHF radio frequencies across valley stations.",
        ],
        "HIGH": [
            "Issue Stage-2 Flash Flood Warning across district wireless network.",
            "Deploy Quick Response Teams (QRT) to inspect vulnerable bridges and culverts.",
            "Alert designated regional shelter wardens and confirm emergency rations.",
            "Advise suspension of pedestrian and vehicular traffic along river causeways.",
            "Prepare mobile emergency medical units for forward deployment.",
        ],
        "CRITICAL": [
            "ACTIVATE EMERGENCY EVACUATION PROTOCOL for low-lying catchment zones.",
            "Sound public warning sirens and broadcast high-priority citizen mobile alerts.",
            "Order immediate closure of river crossings and low-lying bypass corridors.",
            "Direct evacuees along designated high-ground corridors to primary relief shelters.",
            "Request immediate NDRF / SDRF battalion mobilization to staging depots.",
            "Establish forward command post with uninterrupted satellite uplinks.",
        ],
    }

    def get_recommended_actions(self, risk_level: str) -> List[str]:
        return self.ACTION_PROTOCOLS.get(risk_level.upper(), self.ACTION_PROTOCOLS["LOW"])


action_engine = ActionEngine()
