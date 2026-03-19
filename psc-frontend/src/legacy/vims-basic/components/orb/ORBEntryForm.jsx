
import { Button, Card } from './OrbUI';
import DateTimeInput from './DateTimeInput';
import CodeAForm from './CodeAForm';
import CodeBForm from './CodeBForm';
import CodeCForm from './CodeCForm';
import CodeDForm from './CodeDForm';
import CodeFForm from './CodeFForm';
import CodeGForm from './CodeGForm';
import CodeHForm from './CodeHForm';
import CodeIForm from './CodeIForm';

export default function ORBEntryForm({
  formData,
  handleChange,
  handleSubmit,
  setFormData,
  codes,
  availableTanks,
  formatToDateTimeLocal,
  yesterdayDate,
  errors,
  canAccessSelectCode,
}) {
  const { code, details } = formData;

  const dateSection = (
    <DateTimeInput
      id="entry-date"
      label="Entry Date & Time *"
      value={formData.date || ''}
      onChange={val => setFormData(prev => ({ ...prev, date: val }))}
      max={formatToDateTimeLocal(new Date())}
      required
      error={errors.date}
    />
  );

  const sharedProps = {
    details,
    handleChange,
    availableTanks,
    errors,
    formatToDateTimeLocal,
  };

  const renderCodeForm = () => {
    switch (code) {
      case 'A': return <>{dateSection}<CodeAForm {...sharedProps} /></>;
      case 'B': return <>{dateSection}<CodeBForm {...sharedProps} /></>;
      case 'C': return <>{dateSection}<CodeCForm {...sharedProps} /></>;
      case 'D': return <>{dateSection}<CodeDForm {...sharedProps} /></>;
      case 'F': return <>{dateSection}<CodeFForm {...sharedProps} /></>;
      case 'G': return <>{dateSection}<CodeGForm {...sharedProps} /></>;
      case 'H': return <>{dateSection}<CodeHForm {...sharedProps} yesterdayDate={yesterdayDate} handleSubmit={handleSubmit} /></>;
      case 'I': return <>{dateSection}<CodeIForm {...sharedProps} /></>;
      default: return <p>Select a code to begin.</p>;
    }
  };

  const codeOptions = (codes || []).map(c => (
    <option key={c.id} value={c.code}>{c.code} – {c.description}</option>
  ));

  return (
    <Card className='border-0 shadow-none'>
      <form onSubmit={handleSubmit} className="orb-form">
        {canAccessSelectCode && (
        <div className="form-row">
          <label>Select Code *</label>
          <select
            value={formData?.code || ''}
            onChange={e =>
              setFormData(prev => ({ ...prev, code: e.target.value, details: {} }))
            }
          >
            <option value="">Select Code</option>
            {codeOptions}
          </select>
        </div>
        )}

        {code && <div className="form-row">{renderCodeForm()}</div>}

        {code && code !== 'H' && (
          <div className="flex justify-end">
            <Button type="submit">Save Draft</Button>
          </div>
        )}
      </form>
    </Card>
  );
}
