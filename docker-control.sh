#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

case "$1" in
  start)
    echo -e "${GREEN}Starting Weather_ops application in Docker...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Services started!${NC}"
    echo -e "${YELLOW}Frontend available at: http://localhost:8502${NC}"
    echo -e "${YELLOW}Backend API available at: http://localhost:5001${NC}"
    ;;
  stop)
    echo -e "${RED}Stopping Weather_ops application...${NC}"
    docker-compose down
    echo -e "${RED}Services stopped!${NC}"
    ;;
  logs)
    echo -e "${YELLOW}Showing logs for Weather_ops application...${NC}"
    docker-compose logs -f
    ;;
  restart)
    echo -e "${YELLOW}Restarting Weather_ops application...${NC}"
    docker-compose down
    docker-compose up -d
    echo -e "${GREEN}Services restarted!${NC}"
    echo -e "${YELLOW}Frontend available at: http://localhost:8502${NC}"
    echo -e "${YELLOW}Backend API available at: http://localhost:5001${NC}"
    ;;
  build)
    echo -e "${GREEN}Building Weather_ops Docker images...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}Build complete!${NC}"
    ;;
  *)
    echo -e "Usage: $0 {start|stop|logs|restart|build}"
    exit 1
    ;;
esac

exit 0