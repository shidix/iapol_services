#!/bin/bash
source /opt/envs/fastapi/bin/activate
uvicorn ia_services:app --reload --host 0.0.0.0 --port 8001 &
