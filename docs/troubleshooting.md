# Troubleshooting Guide

## Common Issues

### Backend Won't Start

**Issue:** `Address already in use`
**Solution:**
```bash
# Check what's using port 8001
sudo lsof -i :8001
# Kill the process or use different port
kill -9 <PID>
# Or change port in app.py DEFAULT_PORT
```

**Issue:** `ModuleNotFoundError: No module named 'flask'`
**Solution:**
```bash
pip install -r requirements.txt
```

### P1 Can't Connect to Backend

**Issue:** `Connection refused` or timeouts
**Solution:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8001/api/health
   ```
2. Check `PHARMACY_BASE_URL` environment variable:
   ```bash
   echo $PHARMACY_BASE_URL
   ```
3. Check firewall/network:
   ```bash
   telnet localhost 8001
   ```

**Issue:** `CORS errors` in browser console
**Solution:** Backend CORS is configured. If issues persist:
1. Check browser console for exact error
2. Verify backend `add_cors_headers` function is active
3. Try with `curl` to isolate browser vs backend issue

### Database Issues

**Issue:** `SQLite database is locked`
**Solution:**
```bash
# Check for other processes using the database
fuser pharmacy.db
# Kill processes or wait
```

**Issue:** `Table not found`
**Solution:**
```bash
cd test/backend
python init_db.py  # Reinitialize database
```

### Approval API Issues

**Issue:** Approvals not appearing in pending list
**Solution:**
1. Check approval was created successfully
2. Verify approval status is `pending`
3. Check database directly:
   ```bash
   sqlite3 pharmacy.db "SELECT * FROM approvals WHERE status='pending';"
   ```

**Issue:** Can't approve/reject approval
**Solution:**
1. Verify approval exists and is `pending`
2. Check request body includes `doctor_id`
3. For reject, ensure `reason` is provided

## Logging and Debugging

### Enable Debug Logging
**Backend:** Already in debug mode when run with `python app.py`

**P1:** Set log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Backend Logs
```bash
cd test/backend
python app.py 2>&1 | tee backend.log
```

### Check P1 HTTP Traffic
Modify `utils/http_client.py` to log requests:
```python
logger.debug(f"Request: {method} {url}")
logger.debug(f"Response: {response.status_code}")
```

## Performance Issues

### Slow Responses
1. Check backend load with `top` or `htop`
2. Monitor database size: `ls -lh pharmacy.db`
3. Add indexes to frequently queried columns

### High Memory Usage
1. Check for memory leaks in long-running backend
2. Monitor with `ps aux | grep python`
3. Consider restarting backend periodically

## Testing Issues

### Integration Tests Failing
1. Ensure backend is running: `curl http://localhost:8001/api/health`
2. Set `RUN_INTEGRATION_TESTS=1`
3. Check test database is clean: `python init_db.py`

### Mock Tests Failing
1. Verify all mocks are properly configured
2. Check for missing imports in test files
3. Run with `pytest -v` for detailed output

## ROS2 Integration Issues

**Issue:** `ImportError: No module named 'rclpy'`
**Solution:** ROS2 is optional. Backend works without it.

**Issue:** ROS2 tasks not publishing
**Solution:**
1. Verify ROS2 environment is sourced:
   ```bash
   source /opt/ros/humble/setup.bash
   ```
2. Check ROS2 nodes are running
3. Backend logs will show ROS2 status on startup

## Getting Help

1. Check logs for error messages
2. Verify all steps in Integration Guide
3. Test with `curl` to isolate P1 vs backend issues
4. Check database state with `sqlite3 pharmacy.db`

## Emergency Recovery

### Database Corruption
```bash
cd test/backend
mv pharmacy.db pharmacy.db.backup
python init_db.py
```

### Complete Reset
```bash
# Backend
cd test/backend
rm -f pharmacy.db
python init_db.py
python app.py

# P1
cd P1
export PHARMACY_BASE_URL=http://localhost:8001
python -c "import drug_db; drug_db.health_check()"
```