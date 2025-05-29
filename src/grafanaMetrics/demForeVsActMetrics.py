statePayload= {
            "label": "State", "name": "stateName", "type": "select",
            "placeholder": "Select State",
            "reloadMetric": True,
            "options": [
            { "label": "WR", "value": "WRLDCMP.SCADA1.A0047000" } ,  
            { "label": "Maharashtra", "value": "WRLDCMP.SCADA1.A0046980" },
            { "label": "Gujarat", "value": "WRLDCMP.SCADA1.A0046957" },
            { "label": "MP", "value": "WRLDCMP.SCADA1.A0046978" },
            { "label": "Chattisgarh", "value": "WRLDCMP.SCADA1.A0046945" },
            { "label": "Goa", "value": "WRLDCMP.SCADA1.A0046962" }
            ]
        }

#option are not given for dayAheadRevNoPayload, intradayRevNoPayload
revNoPayload={
            "label": "RevNo", "name": "revisionNo", "type": "select",
            "placeholder": "Select Revision No",
            "reloadMetric": True
        }


# options will be fetched dynamcally while calling metric-payload-options endpoint
dayAheadRevNoOptions=  [
            { "__text": "R0A", "__value": "R0A" },
            { "__text": "R0B", "__value": "R0B" },
            ]

intradayRevNoOptions= [
            { "__text": "R1", "__value": "R1" },
            { "__text": "R2", "__value": "R2" },
            { "__text": "R3", "__value": "R3" },
            { "__text": "R4", "__value": "R4" },
            { "__text": "R5", "__value": "R5" },
            { "__text": "R6", "__value": "R6" },
            { "__text": "R7", "__value": "R7" },
            { "__text": "R8", "__value": "R8" },
            { "__text": "R9", "__value": "R9" },
            { "__text": "R10", "__value": "R10" },
            { "__text": "R11", "__value": "R11" },
            { "__text": "R12", "__value": "R12" },
            { "__text": "R13", "__value": "R13" },
            { "__text": "R14", "__value": "R14" },
            { "__text": "R15", "__value": "R15" },
            { "__text": "R16", "__value": "R16" }
            ]