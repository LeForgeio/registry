// Jest setup file
import { generatorService } from '../src/services';

// Close Puppeteer browser after all tests
afterAll(async () => {
  await generatorService.close();
});

// Set longer timeout for tests that use Puppeteer
jest.setTimeout(60000);
