// Install @cubejs-backend/schema-compiler@1.8.14 with its native installer.
// Set NODE_PATH to that installation's node_modules if installed elsewhere.
const fs=require('fs'),path=require('path');
const {compile,PostgresQuery}=require('@cubejs-backend/schema-compiler');
const root=path.resolve(__dirname,'../model/cubes');
(async()=>{
 const repo={localPath:()=>root,dataSchemaFiles:async()=>fs.readdirSync(root).map(n=>({fileName:n,content:fs.readFileSync(path.join(root,n),'utf8')}))};
 const compilers=await compile(repo,{standalone:true});
 const generated={};
 for(const [cube,measure,dimension] of [
  ['ServiceMetrics','closure_30d_rate','borough'],['Policies','row_count','domain'],
  ['PolicyEvidence','row_count','evidence_type'],['PolicyServiceLinks','row_count','agency'],
  ['Socioeconomic','row_count','borough'],['AgencyPerformance','row_count','agency']]){
  const query=compilers.createQuery(PostgresQuery,{measures:[`${cube}.${measure}`],dimensions:[`${cube}.${dimension}`],timezone:'America/New_York'});
  generated[cube]=query.buildSqlAndParams()[0];
 }
 const report={compiler_version:require('@cubejs-backend/schema-compiler/package.json').version,compiled_models:Object.keys(generated),generated_sql:generated,qualification:'Local compilation/SQL generation only; no live Cube deployment or database execution.'};
 fs.writeFileSync(path.resolve(__dirname,'../reports/model-validation.json'),JSON.stringify(report,null,2)+'\n');
 console.log(`Compiled ${Object.keys(generated).length} models and generated PostgreSQL SQL.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
