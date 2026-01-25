#!/bin/bash

cd frontend
npm run dev > frontend.log 2>&1 &

cd ..
cd backend
./start.sh
