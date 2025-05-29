statePayload= {
            "label": "State", "name": "stateName", "type": "select",
            "placeholder": "Select State",
            "reloadMetric": True,
            "options": [
            { "label": "Maharashtra", "value": "WRLDCMP.SCADA1.A0046980" },
            { "label": "Gujarat", "value": "WRLDCMP.SCADA1.A0046957" },
            { "label": "MP", "value": "WRLDCMP.SCADA1.A0046978" },
            { "label": "Chattisgarh", "value": "WRLDCMP.SCADA1.A0046945" },
            { "label": "Goa", "value": "WRLDCMP.SCADA1.A0046962" }
            ]
        }
datePickerPayload = {
    "label": "Date", 
    "name": "selectedDate", 
    "type": "date",
    "placeholder": "Select Date",
    "reloadMetric": True,
    "defaultValue": "today",  # Optional default value
    "format": "YYYY-MM-DD"    # Date format
}

#option are not given for dayAheadRevNoPayload, intradayRevNoPayload
revNoPayload={
            "label": "RevNo", "name": "revisionNo", "type": "select",
            "placeholder": "Select Revision No",
            "reloadMetric": True

        }


# options will be fetched dynamcally while calling metric-payload-options endpoint
dayAheadRevNoOptions=  [
            { "label": "R0A", "value": "R0A" },
            { "label": "R0B", "value": "R0B" },
            ]

intradayRevNoOptions= [
            { "label": "R1", "value": "R1" },
            { "label": "R2", "value": "R2" },
            { "label": "R3", "value": "R3" },
            { "label": "R4", "value": "R4" },
            { "label": "R5", "value": "R5" },
            { "label": "R6", "value": "R6" },
            { "label": "R7", "value": "R7" },
            { "label": "R8", "value": "R8" },
            { "label": "R9", "value": "R9" },
            { "label": "R10", "value": "R10" },
            { "label": "R11", "value": "R11" },
            { "label": "R12", "value": "R12" },
            { "label": "R13", "value": "R13" },
            { "label": "R14", "value": "R14" },
            { "label": "R15", "value": "R15" },
            { "label": "R16", "value": "R16" }
            ]