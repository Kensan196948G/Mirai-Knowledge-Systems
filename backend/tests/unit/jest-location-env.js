/**
 * Custom Jest Environment for Location Navigation
 *
 * jsdom 26 made window.location non-configurable and its href setter
 * triggers real navigation (which is "not implemented" in test env).
 *
 * This custom environment patches LocationImpl.prototype to intercept
 * href get/set and store raw URL values directly — enabling tests to
 * assert window.location.href === '/path' as expected.
 */

const { default: JSDOMEnvironment } = require('jest-environment-jsdom');

class LocationAwareJSDOMEnvironment extends JSDOMEnvironment {
  async setup() {
    await super.setup();

    try {
      const { implSymbol } = require('jsdom/lib/jsdom/living/generated/utils.js');

      // Get the LocationImpl instance via document → docImpl → _location
      const docWrapper = this.global.document;
      const docImpl = docWrapper[implSymbol];
      const locationImpl = docImpl?._location;

      if (!locationImpl) return;

      const locImplProto = Object.getPrototypeOf(locationImpl);
      const hrefDesc = Object.getOwnPropertyDescriptor(locImplProto, 'href');

      // Only patch if configurable (ES6 class prototype accessors are configurable by default)
      if (!hrefDesc?.configurable) return;

      // Store the initial href
      let _rawHref = hrefDesc.get.call(locationImpl);

      // Override href getter/setter on LocationImpl.prototype to bypass navigation
      Object.defineProperty(locImplProto, 'href', {
        get() { return _rawHref; },
        set(v) {
          // Store the raw value exactly as set (e.g. '/login.html')
          // This matches how tests assert window.location.href
          _rawHref = v;
        },
        configurable: true,
        enumerable: hrefDesc.enumerable,
      });
    } catch (e) {
      // Fall back to default behavior if patching fails
    }
  }
}

module.exports = LocationAwareJSDOMEnvironment;
