/** Global localStorage polyfill loaded before all test modules. */
import { installLocalStoragePolyfill } from "./scripts/node_polyfills";

installLocalStoragePolyfill();
