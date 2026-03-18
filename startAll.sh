#!/bin/bash

cd $HOME/test/gestione-affitti
cd frontend
npm run dev > frontend.log 2>&1 &

cd ..
cd backend
./start.sh
