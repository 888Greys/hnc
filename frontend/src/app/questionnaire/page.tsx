'use client';

import { QuestionnaireForm } from '@/components';

export default function QuestionnairePage() {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Digital Legal Questionnaire</h1>
        <p className="text-gray-600">
          Collect comprehensive client information for legal consultation and document generation
        </p>
      </div>

      <QuestionnaireForm />
    </div>
  );
}