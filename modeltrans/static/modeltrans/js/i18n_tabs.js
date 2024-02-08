(() => {
  const currentLanguage = document.documentElement.lang;

  const addEventListeners = ({ defaultField, fields }) => {
    console.info(`Setting up event listeners on fields`, fields);
    const parent = fields[0].closest('.i18n-tabs');

    fields.forEach(field => {
      const fieldLanguage = field.dataset.i18nLang;

      if (field.dataset.i18nDefault) {
        // Synchronize value with the default field
        field.addEventListener('input', () => {
          console.log(`Synchronizing value of ${field.name} with default field`);
          defaultField.value = field.value;
        });
      }

      const tabButton = parent.querySelector(`.i18n-button[data-i18n-lang=${fieldLanguage}]`);
      tabButton.addEventListener('click', () => {
        document.querySelectorAll('.i18n-button').forEach(button => {
          if (button.dataset.i18nLang === fieldLanguage) {
            button.classList.add('active');
          } else {
            button.classList.remove('active');
          }
        });
        document.querySelectorAll('.i18n-tab').forEach(tab => {
          if (tab.dataset.i18nLang === fieldLanguage) {
            tab.classList.remove('hidden');
          } else {
            tab.classList.add('hidden');
          }
        });

        field.focus();
        field.selectionStart = field.value.length;
      });

    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    const i18nFields = document.querySelectorAll('[data-i18n-field]');
    const fieldGroups = {};

    i18nFields.forEach(field => {
      let formset, formsetIndex;
      let groupName = field.dataset.i18nField;

      // Check if we're in a formset
      const formsetsContainer = field.closest('[data-inline-formset]');
      if (formsetsContainer && !formsetsContainer.dataset.formsetListener) {
        formsetsContainer.addEventListener('formset:added', (event) => {
          console.log(`new formset added for group ${groupName}`);

          const formsetContainer = event.target;
          const formsetIndex = event.target.id.match(/\d+/)[0];

          const templateGroup = fieldGroups[groupName];
          const newGroupName = groupName.replace('__prefix__', formsetIndex);

          fieldGroups[newGroupName] = {
            defaultField: formsetContainer.querySelector(`[name=${newGroupName}]`),
            fields: templateGroup.fields.map(field => {
              return formsetContainer.querySelector(`[name=${field.name.replace('__prefix__', formsetIndex)}]`);
            }),
            isTemplate: false,
          };

          // Re-run the script to add tabs to the new formset
          const { defaultField, fields } = fieldGroups[newGroupName];
          addEventListeners({ defaultField, fields });
        });
        formsetsContainer.dataset.formsetListener = true;
      }

      if (formsetsContainer) {
        formset = JSON.parse(formsetsContainer.dataset.inlineFormset);
        // Get current index
        const formsetContainer = field.closest(`[id^=${formset.options.prefix}]`);

        if (formsetContainer.id == `${formset.options.prefix}-empty`) {
          formsetIndex = "__prefix__";
        } else {
          formsetIndex = formsetContainer.id.match(/\d+/)[0];
        }
        groupName = `${formset.options.prefix}-${formsetIndex}-${field.dataset.i18nField}`;
      }

      if (!fieldGroups[groupName]) {
        let selector = `[name=${groupName}]`;
        const defaultField = field.closest('.form-multiline')?.querySelector(selector);

        fieldGroups[groupName] = {
          defaultField: defaultField,
          fields: [],
          isTemplate: formsetIndex === "__prefix__",
        };
      }
      fieldGroups[groupName].fields.push(field);
    });

    for (const group in fieldGroups) {
      const { defaultField, fields, isTemplate } = fieldGroups[group];
      const parent = fields[0].closest('.form-multiline');

      let errorlist = null;
      let helptext = null;
      if (defaultField) {
        const groupLabel = document.createElement('label');
        groupLabel.textContent = defaultField.labels[0].textContent;
        errorlist = parent.querySelector('.errorlist');

        if (defaultField.required) {
          groupLabel.classList.add('required');
        }
        if (defaultField.hasAttribute('aria-describedby')) {
          helptext = document.getElementById(defaultField.getAttribute('aria-describedby'));
        }
        parent.replaceChildren(groupLabel);
      } else {
        console.error(`Error setting up tabs for ${group}, aborting.`);
        continue;
      }

      const tabs = document.createElement('div');
      tabs.classList.add('i18n-tabs');

      const tabButtons = document.createElement('div');
      tabButtons.classList.add('i18n-tab-buttons');
      tabs.appendChild(tabButtons);

      tabs.appendChild(defaultField);
      defaultField.classList.add('hidden');

      fields.forEach(field => {
        const fieldLanguage = field.dataset.i18nLang;

        const tabButton = document.createElement('button');
        tabButton.type = 'button';
        tabButton.classList.add('i18n-button');
        tabButton.dataset.i18nLang = fieldLanguage;
        tabButton.textContent = fieldLanguage;

        const tab = document.createElement('div');
        tab.classList.add('i18n-tab');
        tab.dataset.i18nLang = fieldLanguage;
        if (defaultField.placeholder) {
          field.placeholder = defaultField.placeholder;
        }
        tab.appendChild(field);

        if (field.dataset.i18nDefault && defaultField.ariaInvalid) {
          tabButton.classList.add('errors');
          tab.classList.add('errors');
        }
        tabButtons.appendChild(tabButton);

        // Enable the currently active language
        if (fieldLanguage === currentLanguage) {
          tabButton.classList.add('active');
          //tab.classList.add('active');
        } else {
          tab.classList.add('hidden');
        }
        tabs.appendChild(tab);
      });

      if (!isTemplate) {
        addEventListeners({ defaultField, fields });
      }

      parent.appendChild(tabs);
      if (errorlist) {
        parent.parentNode.insertBefore(errorlist, parent);
      }
      if (helptext) {
        parent.parentNode.appendChild(helptext);
      }
    }
  });

})();
