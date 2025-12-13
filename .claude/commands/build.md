Build the frontend for production deployment.

```bash
cd c:\Users\bored\batch-dashboard\frontend
npm run build
```

## Verify Build Output
```bash
ls -la c:\Users\bored\batch-dashboard\frontend\static\dist\
```

## Test Production Build
After building, access http://localhost:5000 (Flask serves the built files)